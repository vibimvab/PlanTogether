from .models import GroupMember, TravelGroup


def is_group_member(user, group: TravelGroup) -> bool:
    """
        해당 유저가 그룹에 속해 있는지 확인
    """
    return GroupMember.objects.filter(group=group, user=user).exists()


def build_choices(results):
    choices = []
    for r in results:
        if "id" in r and r["id"]:  # 기존 DB Place
            label = f"⭐ {r['name']} ({r.get('address', '')})"
            choices.append((f"existing:{r['id']}", label))
        else:  # 새로 생성할 후보 (Kakao API 결과 등)
            label = f"➕ {r['name']} ({r.get('address', '')})"
            choices.append(("new", label))
    return choices