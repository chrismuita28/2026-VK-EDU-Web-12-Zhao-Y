from django.shortcuts import render

QUESTIONS = [
    {
        "id": i,
        "title": f"question {i}",
        "answers_cnt": i,
        "data": "01.01.2000",
        "likes_cnt": i
    }
    for i in range(3)
]

ANSWERS = [
    {
        "id": i,
        "title": f"question {i}",
        "text": f"text {i}",
        "answers_cnt": i,
        "data": "01.01.2000",
        "time": "18:30",
        "likes_cnt": i
    }
    for i in range(2)
]

def profile(request):
    return render(request, "core/profile.html", context={"questions": QUESTIONS, "answers": ANSWERS})

def user_login(request):
    return render(request, "core/login.html")

def signup(request):
    return render(request, "core/signup.html")
