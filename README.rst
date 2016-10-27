Prism
=====

.. image:: http://forthebadge.com/images/badges/designed-in-ms-paint.svg
    :target: http://forthebadge.com

.. image:: http://forthebadge.com/images/badges/gluten-free.svg
    :target: http://forthebadge.com

.. image:: http://forthebadge.com/images/badges/kinda-sfw.svg
    :target: http://forthebadge.com

Prism is an in-development linux server control panel.

.. image:: http://storage2.static.itmages.com/i/16/0907/h_1473259327_6794757_70c40888cb.png
    :target: https://dl.dropboxusercontent.com/u/62975075/ShareX/2016/09/2016-09-04_15-32-55.mp4
*Hint: click it, it's a video*


Installation
------------
Option 1
    ``curl -O https://raw.githubusercontent.com/CodingForCookies/Prism/master/scripts/install.sh && sh install.sh; rm -f install.sh``
Option 2
    Download scripts/install.sh and run it.
Option 3
    *Warning: Dependencies will need to be manually installed.*

    **You must be using Python 3.**

    Clone the repo and run bin/prism-panel.


Plugin Dev
------------

Take a look at some of the included plugins for an idea on how to use the plugin system!


Dependencies 
------------

* Python 3
* pyOpenSSL >= 16.0.0
* passlib >= 1.6.5
* psutil >= 4.3.0
* SQLAlchemy >= 1.1.0
* flask >= 0.11.1
* Flask-SQLAlchemy >= 2.1
* flask_login >= 0.3.2
* flask_menu >= 0.5.0
