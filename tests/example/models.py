from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy

_ = gettext_lazy


class Article(models.Model):
    site = models.ForeignKey(Site, verbose_name="site", on_delete=models.CASCADE)
    title = models.CharField("article title", max_length=100)
    text = models.TextField(verbose_name="article text")

    class Meta:
        verbose_name = "Site Article"


if True:
    # test that indentation doesn't break ast parser
    class Author(models.Model):
        first_name = models.CharField(max_length=100)
        last_name = models.CharField(max_length=100)


class NestedField(models.Field):
    """Resembles fields like postgres ArrayField."""

    def __init__(self, base_field, **kwargs):
        self.base_field = base_field
        super().__init__(**kwargs)


class ModelFieldVerboseName(models.Model):
    first_arg_name = models.CharField("first arg name [test]")
    kwarg_name = models.CharField(verbose_name="kwarg name [test]")
    arg_gettext = models.CharField(_("arg name [test]"))
    kwargs_gettext = models.CharField(verbose_name=_("kwarg name [test]"))
    gettext_case = models.CharField(verbose_name=_("Kwarg Name [test]"))
    gettext = models.CharField(verbose_name=gettext_lazy("kwarg name [test]"))
    name_related = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="name related test [X050]",
    )
    nested_field = NestedField(
        models.CharField(max_length=100), verbose_name="nested field [X050]"
    )
    no_name = models.CharField()
    no_name_related = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+"
    )
    no_name_nested_field = NestedField(models.CharField(max_length=100))


class ModelFieldFileUploadTo(models.Model):
    image = models.ImageField(upload_to="/path/to/media")
    file = models.FileField(upload_to="/path/to/files")
    image_fail = models.ImageField()
    file_fail = models.FileField()


class CustomTextField(models.TextField):
    pass


class ModelFieldTextNull(models.Model):
    text = models.TextField()
    chars = models.CharField()
    custom = CustomTextField()
    text_fail = models.TextField(null=True)
    chars_fail = models.CharField(null=True)
    custom_fail = CustomTextField(null=True)


class ModelFieldNullFalse(models.Model):
    myfield = models.IntegerField()
    myfield_fail = models.IntegerField(null=False)


class ModelFieldForeignKeyIndex(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="+")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="+")
    another_article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+"
    )
    another_author = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name="+", db_index=True
    )
    filed_one = models.ForeignKey(
        ModelFieldTextNull, on_delete=models.CASCADE, related_name="+", db_index=False
    )
    filed_two = models.ForeignKey(
        ModelFieldNullFalse, on_delete=models.CASCADE, related_name="+", db_index=True
    )

    class Meta:
        unique_together = (("article", "author"), ("field_one", "field_two"))
