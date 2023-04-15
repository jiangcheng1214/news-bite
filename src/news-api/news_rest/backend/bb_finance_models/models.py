# Create your models here.
import sys
from typing import Any, Optional, List, TypeVar, Type, cast, Callable
from enum import Enum


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, float)
    return x


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


class DfpTarget:
    kwl: str
    ni: str
    sites: str
    url: str

    def __init__(self, kwl: str, ni: str, sites: str, url: str) -> None:
        self.kwl = kwl
        self.ni = ni
        self.sites = sites
        self.url = url

    @staticmethod
    def from_dict(obj: Any) -> 'DfpTarget':
        assert isinstance(obj, dict)
        kwl = from_str(obj.get("kwl"))
        ni = from_str(obj.get("ni"))
        sites = from_str(obj.get("sites"))
        url = from_str(obj.get("url"))
        return DfpTarget(kwl, ni, sites, url)

    def to_dict(self) -> dict:
        result: dict = {}
        result["kwl"] = from_str(self.kwl)
        result["ni"] = from_str(self.ni)
        result["sites"] = from_str(self.sites)
        result["url"] = from_str(self.url)
        return result


class AdParams:
    dfp_target: DfpTarget

    def __init__(self, dfp_target: DfpTarget) -> None:
        self.dfp_target = dfp_target

    @staticmethod
    def from_dict(obj: Any) -> 'AdParams':
        assert isinstance(obj, dict)
        dfp_target = DfpTarget.from_dict(obj.get("dfpTarget"))
        return AdParams(dfp_target)

    def to_dict(self) -> dict:
        result: dict = {}
        result["dfpTarget"] = to_class(DfpTarget, self.dfp_target)
        return result

class ContentTag:
    derived_score: float
    direct_score: float
    id: str
    type: str

    def __init__(self, derived_score: float, direct_score: float, id: str, type: str) -> None:
        self.derived_score = derived_score
        self.direct_score = direct_score
        self.id = id
        self.type = type

    @staticmethod
    def from_dict(obj: Any) -> 'ContentTag':
        assert isinstance(obj, dict)
        derived_score = from_float(obj.get("derivedScore"))
        direct_score = from_float(obj.get("directScore"))
        id = from_str(obj.get("id"))
        type = from_str(obj.get("type"))
        return ContentTag(derived_score, direct_score, id, type)

    def to_dict(self) -> dict:
        result: dict = {}
        result["derivedScore"] = to_float(self.derived_score)
        result["directScore"] = to_float(self.direct_score)
        result["id"] = from_str(self.id)
        result["type"] = from_str(self.type)
        return result


class FollowAuthorDetails:
    author_id: int
    author_name: str
    enabled: bool

    def __init__(self, author_id: int, author_name: str, enabled: bool) -> None:
        self.author_id = author_id
        self.author_name = author_name
        self.enabled = enabled

    @staticmethod
    def from_dict(obj: Any) -> 'FollowAuthorDetails':
        assert isinstance(obj, dict)
        author_id = int(from_str(obj.get("authorId")))
        author_name = from_str(obj.get("authorName"))
        enabled = from_bool(obj.get("enabled"))
        return FollowAuthorDetails(author_id, author_name, enabled)

    def to_dict(self) -> dict:
        result: dict = {}
        result["authorId"] = from_str(str(self.author_id))
        result["authorName"] = from_str(self.author_name)
        result["enabled"] = from_bool(self.enabled)
        return result


class ImageURLs:
    default: str
    large: str

    def __init__(self, default: str, large: str) -> None:
        self.default = default
        self.large = large

    @staticmethod
    def from_dict(obj: Any) -> 'ImageURLs':
        assert isinstance(obj, dict)
        default = from_str(obj.get("default"))
        large = from_str(obj.get("large"))
        return ImageURLs(default, large)

    def to_dict(self) -> dict:
        result: dict = {}
        result["default"] = from_str(self.default)
        result["large"] = from_str(self.large)
        return result


class LedeImage:
    caption: str
    credit: str
    image_ur_ls: ImageURLs

    def __init__(self, caption: str, credit: str, image_ur_ls: ImageURLs) -> None:
        self.caption = caption
        self.credit = credit
        self.image_ur_ls = image_ur_ls

    @staticmethod
    def from_dict(obj: Any) -> 'LedeImage':
        assert isinstance(obj, dict)
        caption = from_str(obj.get("caption"))
        credit = from_str(obj.get("credit"))
        image_ur_ls = ImageURLs.from_dict(obj.get("imageURLs"))
        return LedeImage(caption, credit, image_ur_ls)

    def to_dict(self) -> dict:
        result: dict = {}
        result["caption"] = from_str(self.caption)
        result["credit"] = from_str(self.credit)
        result["imageURLs"] = to_class(ImageURLs, self.image_ur_ls)
        return result


class Reading:
    duration_ms: int
    url: str
    voice: str

    def __init__(self, duration_ms: int, url: str, voice: str) -> None:
        self.duration_ms = duration_ms
        self.url = url
        self.voice = voice

    @staticmethod
    def from_dict(obj: Any) -> 'Reading':
        assert isinstance(obj, dict)
        duration_ms = from_int(obj.get("durationMs"))
        url = from_str(obj.get("url"))
        voice = from_str(obj.get("voice"))
        return Reading(duration_ms, url, voice)

    def to_dict(self) -> dict:
        result: dict = {}
        result["durationMs"] = from_int(self.duration_ms)
        result["url"] = from_str(self.url)
        result["voice"] = from_str(self.voice)
        return result


class Topic:
    id: str
    name: str
    referring_id: str

    def __init__(self, id: str, name: str, referring_id: str) -> None:
        self.id = id
        self.name = name
        self.referring_id = referring_id

    @staticmethod
    def from_dict(obj: Any) -> 'Topic':
        assert isinstance(obj, dict)
        id = from_str(obj.get("id"))
        name = from_str(obj.get("name"))
        referring_id = from_str(obj.get("referringId"))
        return Topic(id, name, referring_id)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_str(self.id)
        result["name"] = from_str(self.name)
        result["referringId"] = from_str(self.referring_id)
        return result


class BBFinanceStoriesDetail:
    abstract: List[str]
    ad_params: AdParams
    archived: bool
    attributor: str
    authored_region: str
    brand: str
    byline: str
    card: str
    content_tags: List[ContentTag]
    disable_ads: bool
    follow_author_details: FollowAuthorDetails
    id: str
    internal_id: str
    is_metered: bool
    lede_image: LedeImage
    long_url: str
    newsletter_tout_label: str
    premium: bool
    primary_category: str
    primary_site: str
    published: int
    readings: List[Reading]
    resource_id: str
    resource_type: str
    secondary_brands: List[str]
    security_i_ds: List[str]
    short_url: str
    summary: str
    themed_images: List[Any]
    title: str
    topics: List[Topic]
    type: str
    updated_at: int
    word_count: int

    def __init__(self, abstract: List[str], ad_params: AdParams, archived: bool, attributor: str, authored_region: str, brand: str, byline: str, card: str, content_tags: List[ContentTag], disable_ads: bool, follow_author_details: FollowAuthorDetails, id: str, internal_id: str, is_metered: bool, lede_image: LedeImage, long_url: str, newsletter_tout_label: str, premium: bool, primary_category: str, primary_site: str, published: int, readings: List[Reading], resource_id: str, resource_type: str, secondary_brands: List[str], security_i_ds: List[str], short_url: str, summary: str, themed_images: List[Any], title: str, topics: List[Topic], type: str, updated_at: int, word_count: int) -> None:
        self.abstract = abstract
        self.ad_params = ad_params
        self.archived = archived
        self.attributor = attributor
        self.authored_region = authored_region
        self.brand = brand
        self.byline = byline
        self.card = card
        self.content_tags = content_tags
        self.disable_ads = disable_ads
        self.follow_author_details = follow_author_details
        self.id = id
        self.internal_id = internal_id
        self.is_metered = is_metered
        self.lede_image = lede_image
        self.long_url = long_url
        self.newsletter_tout_label = newsletter_tout_label
        self.premium = premium
        self.primary_category = primary_category
        self.primary_site = primary_site
        self.published = published
        self.readings = readings
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.secondary_brands = secondary_brands
        self.security_i_ds = security_i_ds
        self.short_url = short_url
        self.summary = summary
        self.themed_images = themed_images
        self.title = title
        self.topics = topics
        self.type = type
        self.updated_at = updated_at
        self.word_count = word_count

    @staticmethod
    def from_dict(obj: Any) -> 'BBFinanceStoriesDetail':
        assert isinstance(obj, dict)

        abstract = from_list(from_str, obj.get("abstract"))
        ad_params = AdParams.from_dict(obj.get("adParams"))
        archived = from_bool(obj.get("archived"))
        attributor = from_str(obj.get("attributor"))
        authored_region = from_str(obj.get("authoredRegion"))
        brand = from_str(obj.get("brand"))
        byline = from_str(obj.get("byline"))
        card = from_str(obj.get("card"))
        content_tags = from_list(ContentTag.from_dict, obj.get("contentTags"))
        disable_ads = from_bool(obj.get("disableAds"))
        follow_author_details = FollowAuthorDetails.from_dict(obj.get("followAuthorDetails"))
        id = from_str(obj.get("id"))
        internal_id = from_str(obj.get("internalID"))
        is_metered = from_bool(obj.get("isMetered"))
        lede_image = LedeImage.from_dict(obj.get("ledeImage"))
        long_url = from_str(obj.get("longURL"))
        newsletter_tout_label = from_str(obj.get("newsletterToutLabel"))
        premium = from_bool(obj.get("premium"))
        primary_category = from_str(obj.get("primaryCategory"))
        primary_site = from_str(obj.get("primarySite"))
        published = from_int(obj.get("published"))
        readings = from_list(Reading.from_dict, obj.get("readings"))
        resource_id = from_str(obj.get("resourceId"))
        resource_type = from_str(obj.get("resourceType"))
        secondary_brands = from_list(from_str, obj.get("secondaryBrands"))
        security_i_ds = from_list(from_str, obj.get("securityIDs"))
        short_url = from_str(obj.get("shortURL"))
        summary = from_str(obj.get("summary"))
        themed_images = from_list(lambda x: x, obj.get("themedImages"))
        title = from_str(obj.get("title"))
        topics = from_list(Topic.from_dict, obj.get("topics"))
        type = from_str(obj.get("type"))
        updated_at = from_int(obj.get("updatedAt"))
        word_count = from_int(obj.get("wordCount"))

        return BBFinanceStoriesDetail(abstract, ad_params, archived, attributor, authored_region, brand, byline, card, lede_image, content_tags, disable_ads, follow_author_details, id, internal_id, is_metered, long_url, newsletter_tout_label, premium, primary_category, primary_site, published, readings, resource_id, resource_type, secondary_brands, security_i_ds, short_url, summary, themed_images, title, topics, type, updated_at, word_count)

    def to_dict(self) -> dict:
        result: dict = {}
        result["abstract"] = from_list(from_str, self.abstract)
        result["adParams"] = to_class(AdParams, self.ad_params)
        result["archived"] = from_bool(self.archived)
        result["attributor"] = from_str(self.attributor)
        result["authoredRegion"] = from_str(self.authored_region)
        result["brand"] = from_str(self.brand)
        result["byline"] = from_str(self.byline)
        result["card"] = from_str(self.card)
        result["contentTags"] = from_list(lambda x: to_class(ContentTag, x), self.content_tags)
        result["disableAds"] = from_bool(self.disable_ads)
        result["followAuthorDetails"] = to_class(FollowAuthorDetails, self.follow_author_details)
        result["id"] = from_str(self.id)
        result["internalID"] = from_str(self.internal_id)
        result["isMetered"] = from_bool(self.is_metered)
        result["ledeImage"] = to_class(LedeImage, self.lede_image)
        result["longURL"] = from_str(self.long_url)
        result["newsletterToutLabel"] = from_str(self.newsletter_tout_label)
        result["premium"] = from_bool(self.premium)
        result["primaryCategory"] = from_str(self.primary_category)
        result["primarySite"] = from_str(self.primary_site)
        result["published"] = from_int(self.published)
        result["readings"] = from_list(lambda x: to_class(Reading, x), self.readings)
        result["resourceId"] = from_str(self.resource_id)
        result["resourceType"] = from_str(self.resource_type)
        result["secondaryBrands"] = from_list(from_str, self.secondary_brands)
        result["securityIDs"] = from_list(from_str, self.security_i_ds)
        result["shortURL"] = from_str(self.short_url)
        result["summary"] = from_str(self.summary)
        result["themedImages"] = from_list(lambda x: x, self.themed_images)
        result["title"] = from_str(self.title)
        result["topics"] = from_list(lambda x: to_class(Topic, x), self.topics)
        result["type"] = from_str(self.type)
        result["updatedAt"] = from_int(self.updated_at)
        result["wordCount"] = from_int(self.word_count)
        return result


def bb_finance_stories_detail_from_dict(s: Any) -> BBFinanceStoriesDetail:
    return BBFinanceStoriesDetail.from_dict(s)


def bb_finance_stories_detail_to_dict(x: BBFinanceStoriesDetail) -> Any:
    return to_class(BBFinanceStoriesDetail, x)






