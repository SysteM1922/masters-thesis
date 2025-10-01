
function getSessionName() {
    let url = new URL(window.location.href);
    let pathSegments = url.pathname.split('/');
    // Get the session name
    let sessionname  = pathSegments[pathSegments.length - 1].toLowerCase();
    return sessionname;
}


function loadOnlineFriends() {
    fetch('/getOnlineFriends')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            var onlineFriends = data;
            var container = $('#friendsonline');
            container.empty();

            if (onlineFriends.length == 0) {
                var html = '<p>Não tem amigos online</p>';
                container.append(html);
                return;
            } 

            var html = '';
            for (friend of onlineFriends) {
                html += '<div class="friend">';
                html += '<div class="friend-name">' + friend[1] + '</div>';
                html += '<div class="friend-status"></div>';
                html += '</div>';
            }
            container.append(html);
        })
        .catch(error => {
            console.error('Fetch error:', error);
            return Promise.reject(error);
        });
}



function getOnlineFriends() {
    return fetch('/getOnlineFriends')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(data);
            var onlineFriends = data;
            return onlineFriends;
        })
        .catch(error => {
            console.error('Fetch error:', error);
            return Promise.reject(error);
        });
}


function invitereceived_popup() {
    const popup = document.querySelector('.popup');
    const popupMessage = document.getElementById('popup-message');

    
    const message = 'Convite recebido! A juntar-se à sessão...';	
    popupMessage.textContent = message;
    
    popup.classList.add('show');

    // Hide the popup after 3 seconds
    setTimeout(() => {
        popup.classList.remove('show');
    }, 3000);
}

function joinedroom_popup(name) {
    const popup = document.querySelector('.popup');
    const popupMessage = document.getElementById('popup-message');

    
    const message = name+' juntou-se à sessão!';	
    popupMessage.textContent = message;
    
    popup.classList.add('show');

    // Hide the popup after 3 seconds
    setTimeout(() => {
        popup.classList.remove('show');
    }, 3000);
}





