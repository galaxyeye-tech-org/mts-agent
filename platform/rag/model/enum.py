# -*- coding: utf-8 -*-

from hagworm.extend.struct import Enum, IntEnum


class EnumDocumentStatus(IntEnum):

    Normal = 0
    Progress = 1
    Complete = 2
    Failed = 3

class EnumDocumentNodeType(IntEnum):

    Title = 0
    Paragraph = 1
    Sentence = 2

class EnumTaskStatus(IntEnum):

    Progress = 0
    Complete = 1

