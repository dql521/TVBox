var rule = {
    模板: '自动',
    title: '北川影视',
    host: 'https://www.bcyingshi.ink/fb',
    hostJs: 'print(HOST);let html=request(HOST,{headers:{"User-Agent":PC_UA}});let src=jsp.pdfh(html,"li:eq(2)&&a&&href");print(src);HOST=src',
    searchUrl: '/vodsearch/page/fypage/wd/**/',
    
}