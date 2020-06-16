from django.contrib.sites.models import Site
from django.db import models


class Article(models.Model):
    site = models.ForeignKey(Site, verbose_name="site", on_delete=models.CASCADE)
    title = models.CharField("article title", max_length=100)
    text = models.TextField(verbose_name="article text")

    class Meta:
        verbose_name = "Site Article"


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
