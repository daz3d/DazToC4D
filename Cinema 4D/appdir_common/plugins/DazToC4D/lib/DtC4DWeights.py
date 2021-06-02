import c4d


class Weights:
    subdivsion_level = 0

    def store_subdivision(self, dtu):
        self.subdivsion_level = dtu.get_subdivision()

    def check_level(self):
        if self.subdivsion_level > 0:
            return True

    def auto_calculate_weights(self, body):
        doc = c4d.documents.GetActiveDocument()
        weight_tag = body.GetTag(c4d.Tweights)
        if weight_tag:
            doc.SetActiveTag(weight_tag, c4d.SELECTION_NEW)
            c4d.modules.character.CAWeightMgr.Update(doc)
            c4d.modules.character.CAWeightMgr.SelectAllJoints(doc)
            c4d.modules.character.CAWeightMgr.AutoWeight(doc)
            c4d.EventAdd()
