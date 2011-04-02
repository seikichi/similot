#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from os import path as op
import time
import stat
import string
import re
import math
from optparse import OptionParser
from ConfigParser import SafeConfigParser
import tweepy
import MeCab

CONSUMER_KEY='PsvU2KFpU3XqDpa423uETg'
CONSUMER_SECRET='1fJHhiru2MC0mqCphFvaJUcS4a6cvtf1ADjHOXn1A0'


def main():
    '''entry point'''
    Similot().run()


def _authorization(message):
    '''authorize OAuth'''
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    print(message + (': %s' % auth.get_authorization_url()))
    verifier = raw_input('PIN: ').strip()
    access_token = auth.get_access_token(verifier)
    return access_token


def _get_api(key, secret):
    '''get Tweepy API from key&secret'''
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(key, secret)
    return tweepy.API(auth)


def _document_freq(docs):
    u"""
    >>> _document_freq([{'hoge': 1, 'fuga': 2}, {'piyo':3, 'hoge':1}, {'myo':1, 'fuga':1}]) \\
    ... == {'hoge':2, 'fuga':2, 'piyo':1, 'myo':1}
    True
    """
    df = {}
    for d in docs:
        for w in d.iterkeys():
            df[w] = df.get(w, 0) + 1
    return df


def _cosine_sim(v1, v2):
    u"""
    >>> abs(_cosine_sim({'a':1, 'b':1}, {'a':2, 'c':1})
    ... - 1.0*2.0/(2**0.5*5**0.5)) < 1e-7
    True
    """
    sim = 0
    for key in v1.iterkeys():
        sim += v1[key]*v2.get(key, 0)
    if sim <= 0:
        return sim
    for v in (v1, v2):
        norm = 0
        for val in v.itervalues():
            norm += val*val
        sim /= math.sqrt(norm)
    return sim


def _tf_idf(vec, df, N):
    u"""
    >>> _tf_idf({'hoge':1, 'fuga':2}, {'hoge':5, 'fuga':2, 'myo':10}, 100) \\
    ... == {'hoge':(1.0/3.0)*math.log((100+1)/5), 'fuga':(2.0/3.0)*math.log((100+1)/2)}
    True
    """
    ret = {}
    words = float(sum(vec.itervalues()))
    for (key, val) in vec.iteritems():
        ret[key] = (vec[key]/words) * math.log((N+1)/df[key])
    return ret


def _bag_of_words(post, tagger):
    u""" 
    >>> _bag_of_words('これはひどい', MeCab.Tagger('-Ochasen')) == \\
    ... {u'これ':1, u'は':1, u'ひどい':1}
    True
    """
    if isinstance(post, unicode):
        post = post.encode('utf8')
    post = string.lower(post)
    bow = {}
    node = tagger.parseToNode(post)
    while node:
        word = node.surface.decode('utf8')
        if word:
            bow[word] = bow.get(word, 0) + 1
        node = node.next
    return bow


class Similot(object):
    '''retweet similar posts'''

    def __init__(self):
        self._parse()

        if (self._options.initialize
            or not os.access(self._options.config, os.R_OK)):
            self._initialize_config()
        else:
            self._conf = SafeConfigParser()
            self._conf.read(self._options.config)

        self._api = {}
        for section in ('main', 'bot'):
            self._api[section] = _get_api(self._conf.get(section, 'key'),
                                          self._conf.get(section, 'secret'))
        self._reply_pattern = re.compile('^\.?(@[0-9A-Z_a-z]+\s+)+')
        self._retweet_pattern = re.compile('RT\s+@?[0-9A-Z_a-z]+\s*:?\s+')


    def _preprocess(self, text):
        text = self._reply_pattern.sub('', text)
        text = self._retweet_pattern.sub('', text)
        return text


    def run(self):
        '''main loop'''
        tagger = MeCab.Tagger('-Ochasen')
        max_posts = self._conf.getint('options', 'max_posts')
        update_interval = self._conf.getint('options', 'update_interval')
        recent = self._conf.getint('options', 'recent')
        use_official_retweet = self._conf.getboolean('options', 'use_official_retweet')
        screen_names = {
            'main':self._api['main'].me().screen_name,
            'bot':self._api['bot'].me().screen_name,
        }
        posts, statuses = [], []
        for status in tweepy.Cursor(self._api['main'].home_timeline, count=200).items(max_posts):
            statuses.append(status)
        since_id = statuses[0].id
        statuses.reverse()
        for status in statuses:
            posts.append(_bag_of_words(self._preprocess(status.text), tagger))
        self_posts = [_bag_of_words(self._preprocess(s.text), tagger) for s
                      in self._api['main'].user_timeline(screen_names['main'])][:recent]
        self_posts.reverse()

        while True:
            time.sleep(update_interval)
            try:
                timeline = self._api['main'].home_timeline(since_id=since_id)
                since_id = timeline[0].id
                timeline.reverse() # 新しいのを後ろにする
            except:
                timeline = []

            # filter
            new = [s for s in timeline
                   if s.user.screen_name != screen_names['main'] and
                      s.user.screen_name != screen_names['bot']]

            # update self vec
            for s in (s for s in timeline if s.user.screen_name == screen_names['main']):
                self_posts.append(_bag_of_words(self._preprocess(s.text), tagger))
            self_posts = self_posts[-recent:]

            posts.extend(_bag_of_words(self._preprocess(s.text), tagger) for s in timeline)
            posts = posts[-max_posts:]
            df = _document_freq(posts+self_posts)
            N = len(posts)
            self_posts_ = [_tf_idf(v, df, N) for v in self_posts]

            for s in new:
                vec = _tf_idf(_bag_of_words(self._preprocess(s.text), tagger), df, N)
                sim = -1
                for sp in self_posts_:
                    sim = max(sim, _cosine_sim(vec, sp))
                print sim, s.text
                if sim >= self._conf.getfloat('options', 'threshold'):
                    if use_official_retweet:
                        try:
                            self._api['bot'].retweet(id=s.id)
                        except:
                            pass # privateの場合等
                    else:
                        try:
                            self._api['bot'].update_status((u'RT %s: %s' % (s.user.screen_name, s.text))[:140])
                        except:
                            pass # twitterが死んでる等


    def _parse(self):
        '''parse options'''
        parser = OptionParser()
        parser.add_option("-c",
                          dest="config", default="~/.similot.ini",
                          help="path to the configuration file")
        parser.add_option("-i", "--initialize",
                          action="store_true", dest="initialize", default=False,
                          help="initialize the configration file")
        (options, args) = parser.parse_args()
        options.config = op.expanduser(options.config) # expand '~' to /home/hogefuga
        self._options = options


    def _initialize_config(self):
        '''initialize the config file'''
        self._conf = SafeConfigParser()
        for section in ['main', 'bot', 'options']:
            self._conf.add_section(section)
        for key, val in {'update_interval':'60',
                         'use_official_retweet':'false',
                         'max_posts':'1000',
                         'threshold':'0.15',
                         'recent':'8'}.items():
            self._conf.set('options', key, val)

        for section in ('main', 'bot'):
            token = _authorization("Please authorize us in *%s* account" % section)
            self._conf.set(section, 'key', token.key)
            self._conf.set(section, 'secret', token.secret)

        self._conf.write(open(self._options.config, 'w'))
        os.chmod(self._options.config, stat.S_IRUSR | stat.S_IWUSR)




