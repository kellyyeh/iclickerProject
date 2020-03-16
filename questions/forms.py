from django import forms

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()
    
class homeInput(forms.Form):
    title = forms.CharField(label='', max_length=200,
                              widget=forms.TextInput(attrs={'class' : 'form-control newquestion',
                                                              'name' : 'newquestion',
                                                              'type' : 'text',
                                                              'required' : 'true',
                                                              'placeholder' :'# lecture_ID',
                                                              'style' : 'height: 40px; max-width: 500px; border-radius: 2rem;'
                                                           }))
    type = forms.ChoiceField(choices=[('mc','Multiple Choice'), ('yn','Yes/No'), ('n','Numbered')], widget=forms.RadioSelect)

    anonymous = forms.BooleanField(label='', required=False, widget=forms.CheckboxInput())
    private = forms.BooleanField(label='', required=False, widget=forms.CheckboxInput())

class Choices(forms.Form):
    choice=forms.CharField(label='',max_length=200,
                           widget=forms.TextInput(attrs={'class': 'form-control option',
                                                         'autocomplete': 'off',
                                                         'style': 'width: 90%; border-radius: 0.7rem; background-color: var(--mydarkgrey)',
                           }))

class AdminForm(forms.Form):
    title = forms.CharField(label='', max_length=200,
                              widget=forms.TextInput(attrs={'class' : 'form-control newquestion',
                                                              'name' : 'admin-newquestion',
                                                              'type' : 'text',
                                                              'required' : 'true',
                                                              'placeholder' :'Type a Question',
                                                              'style' : 'height: 40px; max-width: 500px; border-radius: 2rem;'
                                                           }))
