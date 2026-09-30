from ..models import Principal,Step
class Denied(PermissionError): pass
def authorize(p:Principal,s:Step):
    required="manage_journeys" if s.write else "view_journeys"
    if required not in p.permissions: raise Denied(f"requires {required}")
    return {"allowed":True,"approval_required":bool(s.write)}
