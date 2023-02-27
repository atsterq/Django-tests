from django.core.paginator import Paginator

POSTS_AMOUNT = 10


def paginator(request, post_list):
    paginator = Paginator(post_list, POSTS_AMOUNT)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj
