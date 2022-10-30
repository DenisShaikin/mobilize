/*
JS для обработки событий в форме заполнения шин
*/

function encode_params(object) {
    var encodedString = '';
    for (var prop in object) {
        if (object.hasOwnProperty(prop)) {
            if (encodedString.length > 0) {
                encodedString += '&';
            }
            encodedString += encodeURI(prop + '=' + object[prop]);
        }
    }
    return encodedString;
}


/*   Функция меняет статус В Списке, В Наличии */
function changeSelected(id) {
    var element = document.getElementById(id);
/*отправляем на сервер сообщение с id элемента, который надо поменять*/
    var xhr = new XMLHttpRequest();
    xhr.open('post', 'changeItemState');
    xhr.onload = function() {
        if (this.readyState === 4 && this.status === 200) {
        }
        else if (xhr.status !== 200) {
        }
    };
    var csrf_token = document.querySelector('meta[name=csrf-token]').content;
    xhr.setRequestHeader("X-CSRFToken", csrf_token);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.send(JSON.stringify({
        'id': id,
        'value': element.checked }));
}

//Функция должна срабатывать по Enter в новом комментарии (для Item)
function onCommentChange(item_id){
    var element = document.getElementById('newComment');
    var xhr = new XMLHttpRequest();
    xhr.open('post', 'addNewComment');
    xhr.onload = function() {
        if (this.readyState === 4 && this.status === 200) {
            var myResponse = JSON.parse(xhr.responseText);
//            console.log(myResponse.result)
            window.location.reload();
        }
        else if (xhr.status !== 200) {
        }
    };
    var csrf_token = document.querySelector('meta[name=csrf-token]').content;
    xhr.setRequestHeader("X-CSRFToken", csrf_token);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.send(JSON.stringify({
        'item_id': item_id,
        'value': element.value}));
}


//Функция должна срабатывать по Enter в новом комментарии (для Article)
function onArticleCommentChange(article_id){
    var element = document.getElementById('newArticleComment');
    var xhr = new XMLHttpRequest();
    xhr.open('post', 'addNewComment');
    xhr.onload = function() {
        if (this.readyState === 4 && this.status === 200) {
            var myResponse = JSON.parse(xhr.responseText);
//            console.log(myResponse.result)
            window.location.reload();
        }
        else if (xhr.status !== 200) {
        }
    };
    var csrf_token = document.querySelector('meta[name=csrf-token]').content;
    xhr.setRequestHeader("X-CSRFToken", csrf_token);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.send(JSON.stringify({
        'article_id': article_id,
        'value': element.value}));
}


if (document.getElementById('personalPhotoFile')) {
    document.getElementById('personalPhotoFile').addEventListener('change', handlePersonalPhoto, false);
}

function handlePersonalPhoto() {
    var xhr = new XMLHttpRequest();
    xhr.open('post', 'save_personnal_photo', true);
    const fd = new FormData();
    fd.append('persoPhoto', this.files[0]);
    xhr.onload = function() {
        if (this.readyState === 4 && this.status === 200) {
            document.getElementById("personalPhoto").src = JSON.parse(xhr.responseText)['result'];
            document.getElementById("avatar").src = JSON.parse(xhr.responseText)['result'];
            document.getElementById("nav_avatar").src = JSON.parse(xhr.responseText)['result'];

        }
        else if (xhr.status !== 200) {
        }
    };
    var csrf_token = document.querySelector('meta[name=csrf-token]').content;
    xhr.setRequestHeader("X-CSRFToken", csrf_token);
    xhr.send(fd);
}

//Просто реакция на кнупку загрузки файла списка
function handleDownloadListFile() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "downloadItemsFile3", true);
    xhr.onload = function (){
        if (this.readyState === 4 && this.status === 200) {
            var myResponse = JSON.parse(xhr.responseText);
            var element = document.getElementById(myResponse['buttonId']);
            element.click()
        }
        else if (xhr.status !== 200) {
        }
    }
    var csrf_token = document.querySelector('meta[name=csrf-token]').content;
    xhr.setRequestHeader("X-CSRFToken", csrf_token);
    xhr.send();
//    xhr.open('post', 'downloadItemsFile', true);
//    xhr.onload = function() {
//        if (this.readyState === 4 && this.status === 200) {
//
//        }
//        else if (xhr.status !== 200) {
//        }
//    };
//    var csrf_token = document.querySelector('meta[name=csrf-token]').content;
//    xhr.setRequestHeader("X-CSRFToken", csrf_token);
//    xhr.send();
}