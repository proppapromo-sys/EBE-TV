"""Curated home rows (hero + ordered rows, empty/unpublished excluded) and public search."""
from rest_framework.test import APITestCase

from apps.catalog.models import Collection, CollectionItem, Show


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
        # Only the non-empty, published row shows; draft show filtered out of it.
        self.assertEqual([row["title"] for row in r.data["rows"]], ["Originals"])
        self.assertEqual([i["slug"] for i in r.data["rows"][0]["items"]], ["b"])

    def test_rows_are_ordered_by_position(self):
        Collection.objects.create(title="Events", slug="events", position=5)
        ev = Collection.objects.get(slug="events")
        CollectionItem.objects.create(collection=ev, show=self.a, position=0)
        titles = [row["title"] for row in self.client.get("/api/home").data["rows"]]
        self.assertEqual(titles, ["Originals", "Events"])      # position 1 before 5


class SearchViewTests(APITestCase):
    def setUp(self):
        _show("cabaret", "Joseline Cabaret")
        _show("ball", "NowThatsBall")
        _show("secret", "Cabaret Secret", status="draft")     # unpublished

    def test_search_matches_published_only(self):
        r = self.client.get("/api/search", {"q": "cabaret"})
        self.assertEqual(r.status_code, 200)
        slugs = {x["slug"] for x in r.data["results"]}
        self.assertEqual(slugs, {"cabaret"})                   # draft excluded

    def test_empty_query_returns_no_results(self):
        r = self.client.get("/api/search", {"q": "   "})
        self.assertEqual(r.data["results"], [])
