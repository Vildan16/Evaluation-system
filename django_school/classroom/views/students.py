from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import json
import codecs
from collections import Counter
import datetime
import pickle
from ..smartsystem.predict import predict
from django.db import transaction
from django.db.models import Count, Sum
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView
from django.views import View

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
from django.http import HttpResponse

from ..decorators import student_required
from ..forms import StudentInterestsForm, StudentSignUpForm, TakeQuizForm
from ..models import Quiz, Student, TakenQuiz, Question


User = get_user_model()

class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('students:quiz_list')


@method_decorator([login_required, student_required], name='dispatch')
class StudentInterestsView(UpdateView):
    model = Student
    form_class = StudentInterestsForm
    template_name = 'classroom/students/interests_form.html'
    success_url = reverse_lazy('students:quiz_list')

    def get_object(self):
        return self.request.user.student

    def form_valid(self, form):
        messages.success(self.request, 'Interests updated with success!')
        return super().form_valid(form)


@method_decorator([login_required, student_required], name='dispatch')
class QuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'classroom/students/quiz_list.html'

    def get_queryset(self):
        student = self.request.user.student
        taken_quizzes = student.quizzes.values_list('pk', flat=True)
        queryset = Quiz.objects.exclude(pk__in=taken_quizzes) \
            .annotate(questions_count=Count('questions')) \
            .filter(questions_count__gt=0)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['student_subjects'] = self.request.user.student.interests.values_list('pk', flat=True)
        return context

@method_decorator([login_required, student_required], name='dispatch')
class QuizResultsView(View):
    template_name = 'classroom/students/quiz_result.html'

    def get(self, request, *args, **kwargs):        
        quiz = Quiz.objects.get(id = kwargs['pk'])
        taken_quiz = TakenQuiz.objects.filter(student = request.user.student, quiz = quiz)
        if not taken_quiz:
            return render(request, '404.html')
        questions = Question.objects.filter(quiz =quiz)

        return render(request, self.template_name, {'questions':questions, 
            'quiz':quiz, 'percentage': taken_quiz[0].percentage,
                                                    "score" : taken_quiz[0].score,
                                                    "score1": taken_quiz[0].score1,
                                                    "score2": taken_quiz[0].score2,
                                                    "score3": taken_quiz[0].score3,})


@method_decorator([login_required, student_required], name='dispatch')
class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    template_name = 'classroom/students/taken_quiz_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_quizzes \
            .select_related('quiz', 'quiz__subject') \
            .order_by('quiz__name')
        return queryset


@login_required
@student_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    student = request.user.student

    if student.quizzes.filter(pk=pk).exists():
        return render(request, 'students/taken_quiz_form.html')

    total_questions = quiz.questions.count()
    total_questions1 = quiz.questions.filter(type="1").count()
    total_questions2 = quiz.questions.filter(type="2").count()
    total_questions3 = quiz.questions.filter(type="3").count()

    unanswered_questions = student.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_answer = form.save(commit=False)
                student_answer.student = student
                student_answer.save()
                if student.get_unanswered_questions(quiz).exists():
                    return redirect('students:take_quiz', pk)
                else:
                    correct_answers = student.quiz_answers.filter(answer__question__quiz=quiz, answer__is_correct=True).count()
                    correct_answers1 = student.quiz_answers.filter(answer__question__quiz=quiz,
                                                                   answer__question__type="1",
                                                                   answer__is_correct=True).count()

                    correct_answers2 = student.quiz_answers.filter(answer__question__quiz=quiz,
                                                                   answer__question__type="2",
                                                                   answer__is_correct=True).count()

                    correct_answers3 = student.quiz_answers.filter(answer__question__quiz=quiz,
                                                                   answer__question__type="3",
                                                                   answer__is_correct=True).count()

                    percentage1 = round((correct_answers1 / total_questions1) * 100.0, 2)
                    percentage2 = round((correct_answers2 / total_questions2) * 100.0, 2)
                    if total_questions3 == 0:
                        percentage3 = round((percentage1 * percentage2) ** (1 / 2), 2)
                    else:
                        percentage3 = round((correct_answers3 / total_questions3) * 100.0, 2)
                    percentage = round((percentage1 * percentage2 * percentage3) ** (1/3))
                    TakenQuiz.objects.create(student=student, quiz=quiz, score=correct_answers, percentage= percentage,
                                            score1=percentage1, score2=percentage2, score3=percentage3)

                    count = TakenQuiz.objects.filter(student=student).count()

                    if count > 2:
                        student.score *= count - 1
                        student.score1 *= count - 1
                        student.score2 *= count - 1
                        student.score3 *= count - 1


                    student.score += percentage
                    student.score /= count
                    student.score = round(student.score, 2)

                    student.score1 += percentage1
                    student.score1 /= count
                    student.score1 = round(student.score1, 2)

                    student.score2 += percentage2
                    student.score2 /= count
                    student.score2 = round(student.score2, 2)

                    student.score3 += percentage3
                    student.score3 /= count
                    student.score3 = round(student.score3, 2)

                    test = predict(student.score1, student.score2, student.score3)

                    student.predict = test

                    student.save()
                    if percentage < 50.0:
                        messages.warning(request, '???????????????? ??????????! ???????? ??????????????????: %s. \n??????????????: %s \n??????????????????????: %s \n????????????: %s'
                                         % (percentage, percentage1, percentage2, percentage3))
                    else:
                        messages.success(request, '????????????????????! ???????? ??????????????????: %s. \n??????????????: %s \n??????????????????????: %s \n????????????: %s'
                                         % (percentage, percentage1, percentage2, percentage3))
                    return redirect('students:student_quiz_results', pk)
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'classroom/students/take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress,
        'answered_questions': total_questions - total_unanswered_questions,
        'total_questions': total_questions
    })


class StudentList(ListView):
    paginate_by = 36
    template_name = 'classroom/students/student_list.html'
    context_object_name = 'students'

    def get_queryset(self):
        query = self.request.GET.get('q','')
        User = get_user_model()

        queryset = Student.objects.order_by('-score')
        if query:
            queryset = queryset.filter(user__username__icontains = query)
        return queryset

class StudentDetail(View):
    def get(self, request, **kwargs):
        student = Student.objects.get(user_id = kwargs['student'])
        subjects = student.taken_quizzes.all() \
            .values('quiz__subject__name','quiz__subject__color') \
            .annotate(score = Sum('score')) \
            .order_by('-score')
        
        return render(request,'classroom/students/student_detail.html', 
            {'student': student, 'subjects':subjects})

def some_view(request):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sertificate.pdf"'
    now = datetime.datetime.now()

    student = request.user.student

    score = student.score
    reportlab.rl_config.warnOnMissingFontGlyphs = 0

    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

    p = canvas.Canvas(response)
    p.setFont('DejaVuSans', 40)
    p.drawString(170, 700, "????????????????????")
    p.setFont('DejaVuSans', 20)
    p.drawString(90, 650, "???????????? ???????????????????? ????????????????????????, ??????")
    p.drawString(220, 600, str(student.first_name) + " " + str(student.last_name))
    p.drawString(70, 550, '?????????????? ???????? "???????????????????????????? ????????????????????"')
    p.drawString(200, 500, "?? ??????????????????????: " + str(score))

    p.drawString(40, 250, str(now.strftime("%d-%m-%Y")))
    p.drawString(340, 250, "???????????? ??.??. __________")

    p.showPage()
    p.save()

    return response

class StudentMaps(View):

    def get(self, request, **kwargs):
        taken_quiz = TakenQuiz.objects.filter(student=request.user.student)

        unique_section = []
        length = 0
        for x in taken_quiz:
            unique_section.append(str(x.quiz.subject)[7])
            length += 1
        c = Counter(unique_section)
        unique_section = list(set(unique_section))
        unique_section.sort()

        pars = {
            "n": len(unique_section),
        }

        for i in range(1, len(unique_section) + 1):
            pars[f"p{i}"] = c[f"{unique_section[i-1]}"]

        data = {
            "name": "????????",
            "size": 10007,
            "children": []
        }

        a = []
        for i in range(1, pars["n"]+1):
            for j in range(pars[f"p{i}"]):
                a.append(
                    {
                        "name": f"???????????????? {j + 1}", "size": 6807
                    }
                )

            data["children"].append(
                {
                    "name": f"???????????? {i}", "size": 7707, "children": a
                }
            )
            a = []



        with codecs.open('static/css/graph.json', 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=4, ensure_ascii=False)

        if pars["n"] and pars["p1"]:
            return render(request, 'classroom/students/maps.html',
                      {'taken_quiz': taken_quiz, "n_sect": pars["n"], "n_p": pars["p1"]})
        return render(request, 'classroom/students/maps.html',
                      {'taken_quiz': taken_quiz, "n_sect": 0, "n_p": 0})