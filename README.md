[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/PyCQA/pylint)

Media-downloader
--------
is a telegram bot that loads user files.

Features
--------
Data storage location:
 - Loading files into Yandex disk user VK
Vk:
 - Authorization by token
 - Download user's albums
 - Download user's documents 

`
$ wily diff src/ social_nets/DownloadVk.py -r HEAD^1
Using default metrics ['maintainability.mi', 'cyclomatic.complexity', 'raw.loc', 'halstead.h1']
Comparing current with a2ea215 by Coolworld on 2022-04-04.
╒═══════════════════════════╤═════════════════════════╤═════════════════════════╤═════════════════╤═══════════════════╕
│ File                      │ Maintainability Index   │ Cyclomatic Complexity   │ Lines of Code   │ Unique Operands   │
╞═══════════════════════════╪═════════════════════════╪═════════════════════════╪═════════════════╪═══════════════════╡
│ social_nets\DownloadVk.py │ 39.2688 -> 39.1903      │ 61 -> 61                │ 271 -> 272      │ 7 -> 7            │
╘═══════════════════════════╧═════════════════════════╧═════════════════════════╧═════════════════╧═══════════════════╛
`
