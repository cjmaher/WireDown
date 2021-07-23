from django.db import models

# Create your models here.


class EventTable(models.Model):
    NUM_1 = models.CharField(max_length=20)
    FEEDER = models.CharField(max_length=20)
    TYCOD = models.CharField(max_length=20)
    OFF_DTS = models.DateTimeField()
    EVENT_CREATION_TYPE = models.CharField(max_length=30)
    SC = models.CharField(max_length=20)
    XDTS = models.CharField(max_length=20, blank=True, null=True)
    OTHER_EVENTS = models.IntegerField(null=True, blank=True)
    ALARMS = models.IntegerField(null=True, blank=True)
    EID = models.IntegerField(null=True, blank=True)
    PRIORITY = models.CharField(max_length=30)
    LOCATIONS = models.CharField(max_length=100)

    def __str__(self):
        return '{0} {1}'.format(self.NUM_1, self.FEEDER)

    class Meta:
        db_table = 'events'
        verbose_name = 'events'
