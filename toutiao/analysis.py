import jieba
import matplotlib.pyplot as plt
from wordcloud import WordCloud


def getWords():
    with open('article.txt', 'r', encoding='utf -8') as f:
        txt = f.read()
        for i in '~!@#$%^&*()_+-={}|:"<>?[]\;,./—，、。！？ ':
            txt = txt.replace(i, '')
        words = jieba.lcut(txt)
        return words

def wordcloud(words):
    dirty_words = ['新闻', '报料', '全国', '工作', '澎湃', '我们', '会议', '专题', '不得','授权','未经',
                   '不得','转载','4009204009','责任编辑','今年','一个','进行','方面','通过',
                   '校对','相关','可以','关于','同时','一些','表示','就是','作为','需要','这个',
                   '去年','情况','认为','没有','目前','记者','大会','这些','已经','成为','期间','重大',
                   '主要','形成','指出','他们','如何','对于','提交','有关','提供','存在','特别','明确',
                   '现在','应该','包括','很多','时间','其中','以及','自己','过程','我国','国家','部门','通道',
                   '二次','两会','委员','报告','重要']

    new = []
    for word in words:
        if word not in dirty_words:
            new.append(word)

    wl_space_split = " ".join(new)

    backgroud_Image = plt.imread('man.jpg')
    my_wordcloud = WordCloud(mask=backgroud_Image, font_path="Songti.ttc", width=1000, height=700, background_color="white").generate(wl_space_split)
    plt.imshow(my_wordcloud)
    plt.axis("off")
    plt.show()


if __name__ == '__main__':
    words = getWords()

    counts = {}
    for i in words:
        if len(i) >= 2:
            counts[i] = counts.get(i, 0) + 1

    listhills = list(counts.items())
    listhills.sort(key=lambda x: x[1], reverse=True)

    words_new = []
    for i in range(200):
        word, counts = listhills[i]
        print('{0:<10}{1:>5}'.format(word, counts))
        words_new.append(word)

    wordcloud(words_new)
