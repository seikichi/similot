#######
similot
#######

What's this?
============
自分のpostに似たpostをTLから探し，他のアカウントでRTします．

「ラーメン食べたいなー」とpostしたあとに，TLに「ラーメンなら夢語」「夢語はラーメンじゃないだろ……」等の関連してそうな発言を見つけた場合，それを他のアカウント(protected推奨)でRTします．


Requirements
============
* python_ (2.5 or later)
* tweepy_
* mecab-python_ [*]_

.. _python: http://www.python.org/
.. _tweepy: https://github.com/joshthecoder/tweepy
.. _mecab-python: http://mecab.sourceforge.net/bindings.html
.. [*]
   debian系ならpython-mecabとmecab-ipadic-utf8をaptitudeでinstallすれば良い


Installation
============
::

  % python setup.py install

インストールしない場合は同梱の similot.py を利用して下さい．


How to use
=============
::

  % similot

設定ファイル(~/.similot.ini)が無い場合は自動で作成します．OAuthの認証を2回求められますが，1回目は自分のアカウント(このアカウントのTLから類似発言を探します)，2回目はRT用のアカウント(protectedにしておくのをを推奨します)で認証して下さい．


Configuration
=============
~/.similot.ini が設定ファイルです．mainとbotのセクションは手動では変更しないで下さい．以下はoptionsセクションの説明です．

*update_interval*
  更新間隔
*use_official_retweet*
  公式RTを使うかどうか．protectedなアカウントは公式RTできないので(当然ですが)，デフォルトではfalseにしてあります．
*max_posts*
  最大でどれだけの発言を保存しておくか．tf-idfの計算に関わります．分からない場合はデフォルトのままにしておいて下さい．
*threshold*
  しきい値．0.0から1.0 の間の値を設定して下さい．値が多きい程たくさん類似発言を見なします．
*recent*
  類似性の比較に自分の過去の発言をいくつ利用するか


Author
======
* seikichi[at]kmc.gr.jp

License
=======
MIT
