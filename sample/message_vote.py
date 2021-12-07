from datetime import datetime
from datetime import timedelta

import message
import message_admin
import myqq
from schedule import schedule

vote_qq_group = ''
vote_content = ''
vote_schedule_id = 0
vote_cache: dict[str, str] = {}
vote_forbidden_words: list[str] = []


def get_vote_result(count: int = 0) -> str:
    __vote_cache: dict[str, int] = {}
    __vote_cache_reverse: dict[int, list[str]] = {}
    for v in vote_cache.values():
        __vote_cache[v] = __vote_cache.get(v, 0) + 1
    for k, v in __vote_cache.items():
        if v not in __vote_cache_reverse:
            __vote_cache_reverse[v] = []
        __vote_cache_reverse[v].append(k)
    if count > 0:
        s = '目前排名前%d的是：' % count
        i = 0
        for k in sorted(__vote_cache_reverse.keys(), reverse=True):
            for v in __vote_cache_reverse[k]:
                s += '\n%s %d票' % (v, k)
                i += 1
                if i >= count:
                    return s
        return s
    else:
        s = '目前的结果是：'
        for k in sorted(__vote_cache_reverse.keys(), reverse=True):
            for v in __vote_cache_reverse[k]:
                s += '\n%s %d票' % (v, k)
        return s


class AddVote(message.IMessageDispatcher):
    @property
    def name(self) -> str:
        return '发起投票'

    @property
    def tips(self) -> str:
        global vote_schedule_id
        if vote_schedule_id != 0:
            return ''
        return '发起投票 投票内容'

    def __action(self):
        global vote_schedule_id
        dt = datetime.now()
        if dt.hour < 18:
            vote_schedule_id = schedule.add(3600 * 6, self.__action)
        else:
            vote_schedule_id = schedule.add(3600 * 18, self.__action)
        myqq.send_group_message(vote_qq_group, '投票“%s”正在火热进行中，' % vote_content + get_vote_result(3))

    def check_auth(self, qq: str) -> bool:
        return qq in message_admin.admin_cache

    def execute(self, qq_group_number: str, qq: str, *args: str) -> None:
        global vote_content, vote_schedule_id, vote_qq_group
        if vote_schedule_id != 0:
            myqq.send_group_message(qq_group_number, '目前只支持同时存在一个投票，请先停止当前的投票')
            return
        if len(args) < 1:
            myqq.send_group_message(qq_group_number, '指令格式如下：\n发起投票 投票内容')
            return
        vote_qq_group = qq_group_number
        vote_content = ' '.join(args)
        dt = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0) + timedelta(days=1)
        vote_schedule_id = schedule.addabs(dt, self.__action)
        myqq.send_group_message(qq_group_number, '发起“%s”的投票成功' % vote_content)


class DelVote(message.IMessageDispatcher):
    @property
    def name(self) -> str:
        return '确定清除投票'

    @property
    def tips(self) -> str:
        global vote_schedule_id
        if vote_schedule_id == 0:
            return ''
        return '确定清除投票'

    def check_auth(self, qq: str) -> bool:
        return qq in message_admin.admin_cache

    def execute(self, qq_group_number: str, qq: str, *args: str) -> None:
        global vote_qq_group, vote_content, vote_schedule_id, vote_cache
        if len(args) != 0:
            return
        if vote_schedule_id == 0:
            myqq.send_group_message(qq_group_number, '目前没有正在进行的投票')
        else:
            __vote_schedule_id = vote_schedule_id
            vote_qq_group = ''
            vote_content = ''
            vote_schedule_id = 0
            vote_cache = {}
            if schedule.remove(__vote_schedule_id):
                myqq.send_group_message(qq_group_number, '清除投票成功')
            else:
                myqq.send_group_message(qq_group_number, '尽管清除投票成功了，但是貌似出了一些问题，建议检查一下')


class ShowVote(message.IMessageDispatcher):
    @property
    def name(self) -> str:
        return '查看投票'

    @property
    def tips(self) -> str:
        global vote_schedule_id
        if vote_schedule_id == 0:
            return ''
        return '查看投票'

    def check_auth(self, qq: str) -> bool:
        return True

    def execute(self, qq_group_number: str, qq: str, *args: str) -> None:
        global vote_content, vote_schedule_id
        if vote_schedule_id != 0:
            myqq.send_group_message(qq_group_number, '投票“%s”正在火热进行中，' % vote_content + get_vote_result())
        else:
            myqq.send_group_message(qq_group_number, '目前没有正在进行的投票')


class DoVote(message.IMessageDispatcher):
    @property
    def name(self) -> str:
        return '投票'

    @property
    def tips(self) -> str:
        global vote_schedule_id
        if vote_schedule_id == 0:
            return ''
        return '投票 投票答案'

    def check_auth(self, qq: str) -> bool:
        global vote_schedule_id
        return vote_schedule_id != 0

    def execute(self, qq_group_number: str, qq: str, *args: str) -> None:
        if len(args) < 1:
            myqq.send_group_message(qq_group_number, '指令格式如下：\n投票 投票答案')
            return
        global vote_schedule_id, vote_cache, vote_forbidden_words
        if vote_schedule_id == 0:
            myqq.send_group_message(qq_group_number, '目前没有正在进行的投票')
            return
        content = ' '.join(args).strip()
        if '\n' in content:
            return
        try:
            if len(content.encode('gbk')) > 12:
                return
        except ValueError:
            return
        for forbidden_word in vote_forbidden_words:
            if forbidden_word in content:
                myqq.send_group_message(qq_group_number, '“%s”被禁止了' % forbidden_word)
                return
        if qq in vote_cache:
            myqq.send_group_message(qq_group_number, '你将投票结果改为：' + content)
        else:
            myqq.send_group_message(qq_group_number, '你进行了投票：' + content)
        vote_cache[qq] = content


class AddVoteForbiddenWords(message.IMessageDispatcher):
    @property
    def name(self) -> str:
        return '增加投票屏蔽词'

    @property
    def tips(self) -> str:
        global vote_schedule_id
        if vote_schedule_id == 0:
            return ''
        return '增加投票屏蔽词 词语'

    def check_auth(self, qq: str) -> bool:
        return qq in message_admin.admin_cache

    def execute(self, qq_group_number: str, qq: str, *args: str) -> None:
        if len(args) < 1:
            myqq.send_group_message(qq_group_number, '指令格式如下：\n增加投票屏蔽词 词语')
            return
        global vote_schedule_id, vote_cache, vote_forbidden_words
        if vote_schedule_id == 0:
            myqq.send_group_message(qq_group_number, '目前没有正在进行的投票')
            return
        content = ' '.join(args).strip()
        vote_forbidden_words.append(content)
        illegal_vote = []
        for k, v in vote_cache.items():
            if content in v:
                illegal_vote.append(k)
        for k in illegal_vote:
            vote_cache.pop(k)
        myqq.send_group_message(qq_group_number, '投票屏蔽词增加成功，现在的屏蔽词有：\n' + '\n'.join(vote_forbidden_words))


class DelVoteForbiddenWords(message.IMessageDispatcher):
    @property
    def name(self) -> str:
        return '删除投票屏蔽词'

    @property
    def tips(self) -> str:
        global vote_schedule_id
        if vote_schedule_id == 0:
            return ''
        return '删除投票屏蔽词 词语'

    def check_auth(self, qq: str) -> bool:
        return qq in message_admin.admin_cache

    def execute(self, qq_group_number: str, qq: str, *args: str) -> None:
        if len(args) < 1:
            myqq.send_group_message(qq_group_number, '指令格式如下：\n删除投票屏蔽词 词语')
            return
        global vote_schedule_id, vote_forbidden_words
        if vote_schedule_id == 0:
            myqq.send_group_message(qq_group_number, '目前没有正在进行的投票')
            return
        content = ' '.join(args).strip()
        try:
            vote_forbidden_words.remove(content)
            myqq.send_group_message(qq_group_number, '投票屏蔽词删除成功，现在的屏蔽词有：\n' + '\n'.join(vote_forbidden_words))
        except ValueError:
            myqq.send_group_message(qq_group_number, '没有这个屏蔽词')
