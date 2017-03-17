from datetime import date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView
from django.contrib import messages
from django.shortcuts import get_object_or_404

from .models import Projet, Proposition, Offre


class ProjetListView(ListView):
    model = Projet


class ProjetCreateView(LoginRequiredMixin, CreateView):
    model = Projet
    fields = ['nom', 'objectif', 'finances', 'fin_depot', 'fin_achat', 'pict', 'jumbo']

    def form_valid(self, form):
        form.instance.responsable = self.request.user
        messages.success(self.request, 'Votre projet a été correctement créé !')
        return super().form_valid(form)


class ProjetDetailView(DetailView):
    model = Projet

    def get_context_data(self, **kwargs):
        return super().get_context_data(today=date.today(), **kwargs)


class PropositionCreateView(LoginRequiredMixin, CreateView):
    model = Proposition
    fields = ['nom', 'description', 'prix', 'beneficiaires', 'image']

    def form_valid(self, form):
        projet = get_object_or_404(Projet, slug=self.kwargs.get('slug', None))
        form.instance.projet = projet
        form.instance.responsable = self.request.user
        messages.success(self.request, 'Votre proposition a été correctement ajoutée !')
        return super().form_valid(form)


class PropositionDetailView(DetailView):
    model = Proposition

    def get_context_data(self, **kwargs):
        return super().get_context_data(today=date.today(), projet=self.object.projet, **kwargs)


class OffreCreateView(LoginRequiredMixin, CreateView):
    model = Offre
    fields = []

    def get_proposition(self):
        return get_object_or_404(Proposition, slug=self.kwargs.get('slug', None))


    def form_valid(self, form):
        form.instance.proposition = self.get_proposition()
        form.instance.beneficiaire = self.request.user
        messages.success(self.request, 'Votre offre a été correctement ajoutée !')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        projet = get_object_or_404(Projet, slug=self.kwargs.get('p_slug', None))
        return super().get_context_data(projet=projet, proposition=self.get_proposition(), **kwargs)
