"""Curated home rows (hero + ordered rows, empty/unpublished excluded) and public search."""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.catalog.models import Collection, CollectionItem, Show

User = get_user_model()


def _show(slug, title="S", status="published"):
    return Show.objects.create(title=title, slug=slug, status=status,
                               description=f"{title} description")


class HomeViewTests(APITestCase):
    def setUp(self):
        self.a = _show("a", "Alpha")
        self.b = _show("b", "Bravo")
        self.draft = _show("d", "Draft", status="draft")

        hero = Collection.objects.create(title="Featured", slug="featured", kind="hero", position=0)
        CollectionItem.objects.create(collection=hero, show=self.a, position=0)

        row = Collection.objects.create(title="Originals", slug="originals", position=1)
        CollectionItem.objects.create(collection=row, show=self.b, position=0)
        CollectionItem.objects.create(collection=row, show=self.draft, position=1)  # excluded

        # An empty + an unpublished collection — neither should appear.
        Collection.objects.create(title="Empty", slug="empty", position=2)
        hidden = Collection.objects.create(title="Hidden", slug="hidden", position=3,
                                           published=False)
        CollectionItem.objects.create(collection=hidden, show=self.a, position=0)

    def test_home_returns_hero_and_rows(self):
        r = self.client.get("/api/home")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([h["slug"] for h in r.data["hero"]], ["a"])
        # Only the non-empty, published curated row shows; draft show filtered out of it.
        curated = [row for row in r.data["rows"] if row["kind"] == "row"]
        self.assertEqual([row["title"] for row in curated], ["Originals"])
        self.assertEqual([i["slug"] for i in curated[0]["items"]], ["b"])

    def test_rows_are_ordered_by_position(self):
        Collection.objects.create(title="Events", slug="events", position=5)
        ev = Collection.objects.get(slug="events")
        CollectionItem.objects.create(collection=ev, show=self.a, position=0)
        curated = [row["title"] for row in self.client.get("/api/home").data["rows"]
                   if row["kind"] == "row"]
        self.assertEqual(curated, ["Originals", "Events"])     # position 1 before 5


class PosterFallbackTests(APITestCase):
    def test_card_poster_falls_back_to_hero_then_episode_thumb(self):
        from apps.catalog.models import Episode, Season
        # No poster, but a hero → uses hero.
        h = Show.objects.create(title="H", slug="h", status="published",
                                hero_url="https://img/hero.jpg")
        # No poster, no hero, but a published episode with a thumbnail → uses that.
        t = Show.objects.create(title="T", slug="t", status="published")
        season = Season.objects.create(show=t, number=1)
        Episode.objects.create(season=season, number=1, title="E1", status="published",
                               thumbnail_url="https://img/ep.jpg")
        col = Collection.objects.create(title="Row", slug="row", position=0)
        CollectionItem.objects.create(collection=col, show=h, position=0)
        CollectionItem.objects.create(collection=col, show=t, position=1)

        items = {i["slug"]: i for i in self.client.get("/api/home").data["rows"][0]["items"]}
        self.assertEqual(items["h"]["poster_url"], "https://img/hero.jpg")
        self.assertEqual(items["t"]["poster_url"], "https://img/ep.jpg")


class AutoRowsTests(APITestCase):
    def test_new_on_ebe_row_appears(self):
        a = _show("a", "Alpha")
        col = Collection.objects.create(title="Row", slug="row", position=0)
        CollectionItem.objects.create(collection=col, show=a, position=0)
        titles = [r["title"] for r in self.client.get("/api/home").data["rows"]]
        self.assertIn("New on EBE", titles)

    def test_continue_watching_only_for_authed_user_with_progress(self):
        from apps.catalog.models import Episode, Season, WatchProgress
        user = User.objects.create_user("w@ebe.tv", "pw12345678")
        show = _show("z", "Zeta")
        season = Season.objects.create(show=show, number=1)
        ep = Episode.objects.create(season=season, number=1, title="E1", status="published")
        WatchProgress.objects.create(user=user, episode=ep, position_s=120)
        # Anonymous: no Continue Watching.
        self.assertNotIn("Continue Watching",
                         [r["title"] for r in self.client.get("/api/home").data["rows"]])
        # Authed with progress: present.
        self.client.force_authenticate(user)
        self.assertIn("Continue Watching",
                      [r["title"] for r in self.client.get("/api/home").data["rows"]])


class SearchViewTests(APITestCase):
    def setUp(self):
        s = _show("cabaret", "Joseline Cabaret")
        s.genre = ["Reality"]; s.save()
        d = _show("drama1", "City Drama")
        d.genre = ["Drama"]; d.save()
        _show("secret", "Cabaret Secret", status="draft")     # unpublished

    def test_search_matches_published_only(self):
        r = self.client.get("/api/search", {"q": "cabaret"})
        self.assertEqual(r.status_code, 200)
        slugs = {x["slug"] for x in r.data["results"]}
        self.assertEqual(slugs, {"cabaret"})                   # draft excluded

    def test_empty_query_returns_facets_no_results(self):
        r = self.client.get("/api/search", {"q": "   "})
        self.assertEqual(r.data["results"], [])
        self.assertEqual(set(r.data["genres"]), {"Reality", "Drama"})

    def test_genre_filter(self):
        r = self.client.get("/api/search", {"genre": "Drama"})
        self.assertEqual({x["slug"] for x in r.data["results"]}, {"drama1"})
