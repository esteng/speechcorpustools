import os
import pytest

from speechtools.corpus import CorpusContext

from polyglotdb.graph.func import Sum

def test_encode_pause(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        discourse = g.discourse('acoustic_corpus')
        g.encode_pauses(['sil'])
        q = g.query_graph(g.pause)
        print(q.cypher())
        assert(len(q.all()) == 11)

        paused = g.discourse('acoustic_corpus')
        expected = [x for x in discourse if x.label != 'sil']
        for i,d in enumerate(expected):
            print(d.label, paused[i].label)
            assert(d.label == paused[i].label)

        g.reset_pauses()
        new_discourse = g.discourse('acoustic_corpus')
        for i,d in enumerate(discourse):
            assert(d.label == new_discourse[i].label)

        g.encode_pauses(['sil','um','uh'])
        q = g.query_graph(g.pause)
        print(q.cypher())
        assert(len(q.all()) == 14)

        paused = g.discourse('acoustic_corpus')
        expected = [x for x in discourse if x.label not in ['sil','um','uh']]
        for i,d in enumerate(expected):
            print(d.label, paused[i].label)
            assert(d.label == paused[i].label)

        g.reset_pauses()
        new_discourse = g.discourse('acoustic_corpus')
        print(discourse)
        print(new_discourse)
        for i,d in enumerate(discourse):
            assert(d.label == new_discourse[i].label)


def test_query_with_pause(acoustic_config):
    with CorpusContext(acoustic_config) as g:
        g.encode_pauses(['sil', 'uh','um'])
        q = g.query_graph(g.word).filter(g.word.label == 'cares')
        q = q.columns(g.word.following.label.column_name('following'),
                    g.pause.following.label.column_name('following_pause')).order_by(g.word.begin)

        results = q.aggregate(Sum(g.pause.following.duration).column_name('following_pause_duration'))
        print(q.cypher())
        assert(len(results) == 1)
        assert(results[0].following == 'this')
        assert(results[0].following_pause == ['sil','um'])
        assert(abs(results[0].following_pause_duration - 1.035027) < 0.001)

        q = g.query_graph(g.word).filter(g.word.label == 'this')
        q = q.columns(g.word.previous.label.column_name('previous'),
                    g.pause.previous.label.column_name('previous_pause'),
                    g.pause.previous.begin,
                    g.pause.previous.end).order_by(g.word.begin)
        results = q.aggregate(Sum(g.pause.previous.duration).column_name('previous_pause_duration'))
        print(q.cypher())
        assert(len(results) == 2)
        assert(results[1].previous == 'cares')
        assert(results[1].previous_pause == ['sil','um'])
        assert(abs(results[1].previous_pause_duration - 1.035027) < 0.001)

        g.encode_pauses(['sil'])
        q = g.query_graph(g.word).filter(g.word.label == 'words')
        q = q.columns(g.word.following.label.column_name('following'),
                    g.pause.following.label.column_name('following_pause')).order_by(g.word.begin)
        q = q.order_by(g.word.begin)
        results = q.aggregate(Sum(g.pause.following.duration).column_name('following_pause_duration'))
        print(q.cypher())
        assert(len(results) == 5)
        assert(results[0].following == 'and')
        assert(results[0].following_pause == ['sil'])
        assert(abs(results[0].following_pause_duration - 1.152438) < 0.001)
