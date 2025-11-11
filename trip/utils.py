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