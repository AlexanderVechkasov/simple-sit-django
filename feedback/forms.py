"""Форма обратной связи."""

from django import forms

from .models import FeedbackMessage


class FeedbackForm(forms.ModelForm):
    """Почта и текст сообщения. Проверки длины и формата почты Django
    берёт из модели, а свои тексты ошибок задаём ниже — по-человечески."""

    # Honeypot: скрытое поле-ловушка для спам-ботов.
    homepage = forms.CharField(
        label="Не заполняйте это поле",
        required=False,
        widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}),
    )

    class Meta:
        model = FeedbackMessage
        fields = ["email", "message"]
        labels = {
            "email": "Ваша почта",
            "message": "Сообщение",
        }
        help_texts = {
            "email": "Только чтобы ответить вам. Никуда не передаётся.",
            "message": "Ошибка в статье, дополнение, идея нового события — всё пригодится.",
        }
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "message": forms.Textarea(attrs={"rows": 6}),
        }
        error_messages = {
            "email": {
                "required": "Укажите почту, чтобы мы могли ответить.",
                "invalid": "Проверьте адрес: нужен вид name@mail.ru.",
            },
            "message": {
                "required": "Напишите сообщение.",
            },
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)

    def clean_message(self):
        """Своя проверка поля message: убираем пробелы по краям и не
        принимаем совсем короткие сообщения вроде «привет»."""
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Сообщение слишком короткое — напишите хотя бы пару слов.")
        return message

    def is_spam(self):
        """Ловушка заполнена — значит, форму отправил бот."""
        return bool(self.cleaned_data.get("homepage"))
