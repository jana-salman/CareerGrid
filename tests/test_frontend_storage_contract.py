from services.simulation_storage import get_user_visible_evaluation


def test_readiness_is_part_of_public_report_but_unknown_fields_are_not():
    public = get_user_visible_evaluation({"overall_score":80,"summary":"Good","frontend_readiness":"Ready","private_notes":"secret"})
    assert public["frontend_readiness"] == "Ready"
    assert "private_notes" not in public

