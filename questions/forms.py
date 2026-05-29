from django import forms
from questions.models import Question, Answer, Tag

class AskForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'id': 'id_tags', 'placeholder': 'python, django, html (через запятую)'}),
        help_text="До 5 тегов, каждый максимум 20 символов. Разделяйте запятыми.")

    class Meta:
        model = Question
        fields = ['title', 'text']
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'id_title', 'placeholder': 'Кратко опишите суть проблемы'}),

            'text': forms.Textarea(
                attrs={'class': 'form-control', 'id': 'id_text', 'rows': 8, 'placeholder': 'Опишите проблему детально'})}

    def clean_tags_input(self):
        tags_str = self.cleaned_data.get('tags_input', '')
        raw_tags = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
        
        if len(raw_tags) > 5:
            raise forms.ValidationError("Можно указать не более 5 тегов.")
        
        for tag_name in raw_tags:
            if len(tag_name) > 20:
                raise forms.ValidationError(f"Тег '{tag_name}' слишком длинный (макс. 20 символов).")
        return raw_tags

    def save(self, commit=True, author=None):
        question = super().save(commit=False)
        if author:
            question.author = author
        if commit:
            question.save()
            
        tag_names = self.cleaned_data.get('tags_input', [])
        if tag_names:
            tags_to_add = []
            for name in tag_names:
                tag_obj, _ = Tag.objects.get_or_create(name=name)
                tags_to_add.append(tag_obj)
            question.tags.set(tags_to_add)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']
        widgets = {'text': forms.Textarea(
            attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Напишите ваш ответ...', 'required': True})}
    
    def clean_text(self):
        text = self.cleaned_data.get('text')
        if text is None:
            raise forms.ValidationError("Это поле обязательно.")
        if len(text.strip()) < 10:
            raise forms.ValidationError("Ответ слишком короткий. Напишите что-то более подробное.")
        return text
    
    def save(self, commit=True, question=None, author=None):
        answer = super().save(commit=False)
        if question:
            answer.question = question
        if author:
            answer.author = author
        if commit:
            answer.save()
        return answer
