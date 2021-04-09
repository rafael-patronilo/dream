from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component
from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.common.file import load_pickle


@register("q_to_page")
class QToPage(Component):
    def __init__(self, q_to_page_filename, entities_num=5, **kwargs):
        self.q_to_page = load_pickle(str(expand_path(q_to_page_filename)))
        self.entities_num = entities_num

    def __call__(self, entities_batch):
        pages_batch = []
        for entities_list in entities_batch:
            if entities_list:
                pages_list = []
                for entities in entities_list:
                    pages = []
                    if entities:
                        for entity in entities[:self.entities_num]:
                            page = self.q_to_page.get(entity, "")
                            if page:
                                pages.append(page)
                    pages_list.append(pages)
                pages_batch.append(pages_list)
            else:
                pages_batch.append([])

        return pages_batch