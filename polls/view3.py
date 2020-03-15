'''from django.shortcuts import redirect

def login_success(request):
    """
    Redirects users based on whether they are in the admins group
    """
    if request.user.groups.filter(name="admins").exists():
        # user is an admin
        return redirect("/professor_home")
    else:
        return redirect("/student_home") 
'''