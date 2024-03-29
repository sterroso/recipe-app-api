"""
Tests for the ingredients API.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingredient,
    Recipe,
)

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Creates and returns an ingredient-detail url."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='testuser@example.com', password='testpass123'):
    """Creates and returns a test user."""
    return get_user_model().objects.create_user(
        email=email,
        password=password,
    )


class PublicIngredientsAPITests(TestCase):
    """Tests for unauthenticated ingredients API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Tests auth is required for retrieving ingredients."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """Tests authenticated ingredients API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Tests retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name='Mumu')
        Ingredient.objects.create(user=self.user, name='Ajo')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Tests list of ingredients is limited to authenticated user."""
        user2 = create_user(email='uase2@example.com')
        Ingredient.objects.create(user=user2, name='Pimienta')
        ingredient = Ingredient.objects.create(user=self.user, name='Jalapeño')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """Tests updating an ingredient."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Paprika',
        )

        payload = {'name': 'Pimentón'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name='Mango',
        )
        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_assigned_to_recipes(self):
        """Tests listing ingredients by those assigned to recipes."""
        in1 = Ingredient.objects.create(user=self.user, name='Tortilla')
        in2 = Ingredient.objects.create(user=self.user, name='Nopales')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Chilaquiles',
            time_minutes=28,
            price=Decimal('78.25'),
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Tests filtered ingredients returns a unique list."""
        ing = Ingredient.objects.create(user=self.user, name='Huevos')
        Ingredient.objects.create(user=self.user, name='Fresas')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Huevos motuleños',
            price=Decimal('65.23'),
            time_minutes=12,
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Huevos divorciados',
            price=Decimal('58.99'),
            time_minutes=9,
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
