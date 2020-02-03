"""Main models."""
from datetime import date

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from ndh.models import Links, NamedModel, TimeStampedModel
from ndh.utils import query_sum


def upload_to_proj(instance, filename):
    """Set upload path for Cagnotte images."""
    return f'cagnottesolidaire/proj_{instance.slug}.' + filename.split('.')[-1]


def upload_to_prop(instance, filename):
    """Set upload path for Proposition images."""
    return f'cagnottesolidaire/proj_{instance.cagnotte.slug}_prop_{instance.slug}.' + filename.split('.')[-1]


def validate_positive(value):
    """Validate value >= 0."""
    if value < 0:
        raise ValidationError(f'{value} n’est pas positif')


def validate_future(value):
    """Validate value >= today."""
    if value < date.today():
        raise ValidationError(f'{value} est déjà passé')


class Cagnotte(Links, TimeStampedModel, NamedModel):
    """Model for a Cagnotte."""
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    image = models.ImageField('Image', upload_to=upload_to_proj, blank=True)
    objectif = models.TextField('Description de l’objectif de la cagnotte')
    finances = models.DecimalField('But à atteindre', max_digits=8, decimal_places=2, validators=[validate_positive])
    fin_depot = models.DateField('Date de fin du dépôt des propositions', validators=[validate_future])
    fin_achat = models.DateField('Date de fin des achats', validators=[validate_future])

    def offres(self):
        """Get valid Offres for this Cagnotte."""
        return Offre.objects.filter(proposition__cagnotte=self, valide=True)

    def somme(self):
        """Get the sum of the prices for the valid Offres of this Cagnotte."""
        return query_sum(self.offres(), 'prix')

    def somme_encaissee(self):
        """Get the sum of the prices for the valid and payed Offres of this Cagnotte."""
        return query_sum(self.offres().filter(paye=True), 'prix')

    def progress(self):
        """Get the advancement in percent of the goal for this Cagnotte."""
        return int(round(100 * self.somme() / self.finances))

    @property
    def responsable_s(self):
        """Get the name of the responsable of this Cagnotte as a string."""
        return self.responsable.get_short_name() or self.responsable.get_username()


class Proposition(Links, TimeStampedModel, NamedModel):
    """Model for a Proposition on a Cagnotte."""
    cagnotte = models.ForeignKey(Cagnotte, on_delete=models.PROTECT)
    responsable = models.ForeignKey(User, on_delete=models.PROTECT)
    description = models.TextField()
    prix = models.DecimalField(max_digits=8, decimal_places=2, validators=[validate_positive])
    beneficiaires = models.IntegerField('Nombre maximal de bénéficiaires',
                                        default=1,
                                        validators=[validate_positive],
                                        help_text='0 pour un nombre illimité')
    image = models.ImageField('Image', upload_to=upload_to_prop, blank=True)

    class Meta:
        """Meta definitions."""
        ordering = ('cagnotte', 'prix')

    def get_absolute_url(self):
        """Get the url of this Proposition."""
        return reverse('cagnottesolidaire:proposition', kwargs={'slug': self.slug, 'p_slug': self.cagnotte.slug})

    def offres(self):
        """Get a list of [all, valid, payed] Offres for this Proposition."""
        return [self.offre_set.filter(**f).count() for f in [{}, {'valide': True}, {'paye': True}]]

    def offrable(self):
        """Tell if this Proposition is available."""
        if date.today() > self.cagnotte.fin_achat:
            return False
        return self.beneficiaires == 0 or self.offre_set.filter(valide=True).count() < self.beneficiaires

    def somme(self):
        """Get the sum of all Offres for this Proposition."""
        return query_sum(self.offre_set.filter(valide=True), 'prix')

    @property
    def ben_s(self):
        """Get the number of beneficiaires for this Proposition as a string."""
        return str(self.beneficiaires or '∞')

    @property
    def responsable_s(self):
        """Get the name of the responsable of this Proposition as a string."""
        return self.responsable.get_short_name() or self.responsable.get_username()


class Offre(Links, models.Model):
    """Model for an Offre on a Proposition."""
    proposition = models.ForeignKey(Proposition, on_delete=models.PROTECT)
    beneficiaire = models.ForeignKey(User, on_delete=models.PROTECT)
    valide = models.NullBooleanField('validé', default=None)
    paye = models.BooleanField('payé', default=False)
    remarques = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=8, decimal_places=2, validators=[validate_positive])

    class Meta:
        """Meta definitions."""
        ordering = ('paye', 'valide', 'proposition')

    def __str__(self):
        """Format this Offre as a string."""
        return f'offre de {self.beneficiaire} sur {self.proposition} (cagnotte {self.proposition.cagnotte})'

    def get_absolute_url(self):
        """Get the url of the Proposition of this Offre."""
        return self.proposition.get_absolute_url()

    @property
    def responsable_s(self):
        """Get the name of the responsable of the Proposition of this Offre as a string."""
        return self.proposition.responsable_s

    @property
    def beneficiaire_s(self):
        """Get the name of the bénéficiaire for this Offre as a string."""
        return self.beneficiaire.get_short_name() or self.beneficiaire.get_username()


class Demande(models.Model):
    """Model for a Demande on a Cagnotte."""
    cagnotte = models.ForeignKey(Cagnotte, on_delete=models.PROTECT)
    demandeur = models.ForeignKey(User, on_delete=models.PROTECT)
    description = models.CharField(max_length=250)

    def __str__(self):
        """Return the description of this Demande."""
        return self.description

    def get_absolute_url(self):
        """Return the url of the Cagnotte for this Demande."""
        return self.cagnotte.get_absolute_url()
