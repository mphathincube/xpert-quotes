from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Car(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='cars')
    car_reg = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car_reg} - {self.client.name}"


class Quote(models.Model):
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='quotes')
    car = models.ForeignKey(Car, on_delete=models.SET_NULL,
                            null=True, blank=True, related_name='quotes')
    service = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote for {self.service} - {self.client.name}"
