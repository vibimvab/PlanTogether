from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # 가입 후 자동 로그인
            return redirect("trip:index")

    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


if __name__ == '__main__':
    print(str(SignUpForm))