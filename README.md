现在这几个脚本，只有学堂在线的可以使用，其他的已经失效，日后有时间再尝试修正。
cn_mooc_dl
==========
用于下载学堂在线上的课程视频和字幕，仅限于学习目的。
支持断点续传，多线程下载，线程初始为10个线程。

2. 清华学堂在线（`xuetangx.com`）视频下载

####测试环境：   `PYTHON 2.7； WIN 10`
####依赖包： `requests， beautifulsoup4`
	pip install requests
	pip install beautifulsoup4
或者在代码目录下
	
	pip install -r requirements.txt 



####清华学堂在线（`xuetangx.com`）：    
    python xuetangx_dl.py  -f cookie.txt "url"
    
* 其中 url 是课程课件页面的浏览器地址，比如：
`http://www.xuetangx.com/courses/TsinghuaX/30240243X/2015_T1/courseware/14def9edc58e4936abd418333f899836/`
登陆改用cookie文件，这样可以不受网站修改登录验证的影响，不需要经常维护，不需要输入用户名和密码，参考了coursera-dl但是插件使用的是[Cookie Inspector](https://chrome.google.com/webstore/detail/cookie-inspector/jgbbilmfbammlbbhmmgaagdkbkepnijn?utm_source=chrome-app-launcher-info-dialog)。
首先用浏览器登陆学堂在线，然后用Cookie Inspector 导出cookies(导出的方法是：安装好插件后，按照插件说明的方式在chrome里打开检查元素，即可以看到cookies，然后右键导出cookies。)。然后在命令中加入 -f 导出的cookie文件名。




#####--path 用于指定保存文件夹， --overwrite 指定是否覆盖


