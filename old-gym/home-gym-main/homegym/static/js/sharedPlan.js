function getPlanNumber() {
    let url = new URL(window.location.href);
    let pathSegments = url.pathname.split('/');
    // Get the plan number
    let planNumber = parseInt(pathSegments[pathSegments.length - 1].replace(/\D/g, ''));
    return planNumber;
}


function loadPlanHead_2(planNumber) {

    return fetch('/planotreino/' + planNumber)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            var container = $('#content');
            container.empty();
            var planDetails = data[0]
            // inicio do cabeçalho
            var html = '<div class="maindiv">';
            html += '<div id="microphone"> <svg class="mic" id="mic" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width:70px; height:70px;"> <path fill="#000000" d="M12,1A4,4 0 0,1 16,5V11A4,4 0 0,1 12,15A4,4 0 0,1 8,11V5A4,4 0 0,1 12,1M12,19A7,7 0 0,0 19,12H22A10,10 0 0,1 12,22A10,10 0 0,1 2,12H5A7,7 0 0,0 12,19Z" /></svg> </div>'; 
            html += '<div class="Info">';
            html += '<div class="IMGcontainer"><img src=../' + planDetails[4] + ' class="meusplanosimg" ></div>';
            html += '<div class="text">'
            html += '<h3>' + planDetails[0] + '</h3>';
            html += '<div class="horizontal-line"></div>';
            html += '<div class="dn"><h3 class="PlanNumber">Plano ' + planNumber + '</h3> <div class="streak_level_group"><div id="level"></div><div id="streak"></div></div></div></div>'; //level
            html += '<p id="datetime" class="datetime-container"><span class="time"></span><span class="date"></span></p></div></div>';
            
            container.append(html);
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });

}


function loadPlanInfo_2(planNumber) {
    return fetch('/planotreino/' + planNumber)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            var mmiCli_1 = null;
            mmiCli_1 = new MMIClient(null, "https://" + host + ":8000/IM/USER1/APPSPEECH");
            sendToVoice("Plano " + planNumber);
            function sendToVoice(texto) {
                //let speak = "&lt;speak version=\"1.0\" xmlns=\"http://www.w3.org/2001/10/synthesis\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.w3.org/2001/10/synthesis http://www.w3.org/TR/speech-synthesis/synthesis.xsd\" xml:lang=\"pt-PT\"&gt;&lt;p&gt;" + "quadrado" + "&lt;/p&gt;&lt;/speak&gt";
                let speak = "<speak version=\"1.0\" xmlns=\"http://www.w3.org/2001/10/synthesis\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.w3.org/2001/10/synthesis http://www.w3.org/TR/speech-synthesis/synthesis.xsd\" xml:lang=\"pt-PT\"><p>" + texto + "</p></speak>";
                var result = speak;
                mmiCli_1.sendToIM(new LifeCycleEvent("APPSPEECH", "IM", "text-1", "ctx-1").
                    doStartRequest(new EMMA("text-", "text", "command", 1, 0).
                        setValue(JSON.stringify(result))));
            }
            var container = $('#content');
            container.empty();
            var planDetails = data[0]
            var exercises = data[1]
            // inicio do cabeçalho
            var html = '<div class="maindiv">';
            html += '<div id="microphone"> <svg class="mic" id="mic" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width:70px; height:70px;"> <path fill="#000000" d="M12,1A4,4 0 0,1 16,5V11A4,4 0 0,1 12,15A4,4 0 0,1 8,11V5A4,4 0 0,1 12,1M12,19A7,7 0 0,0 19,12H22A10,10 0 0,1 12,22A10,10 0 0,1 2,12H5A7,7 0 0,0 12,19Z" /></svg> </div>'; 
            html += '<div class="Info">';
            html += '<div class="IMGcontainer"><img src=../' + planDetails[4] + ' class="meusplanosimg" ></div>';
            html += '<div class="text">'
            html += '<h3>' + planDetails[0] + '</h3>';
            html += '<div class="horizontal-line"></div>';
            html += '<div class="dn"><h3 class="PlanNumber">Plano ' + planNumber + '</h3> <div class="streak_level_group"><div id="level"></div><div id="streak"></div></div></div></div>'; //leve
            html += '<p id="datetime" class="datetime-container"><span class="time"></span><span class="date"></span></p></div></div>';
            // fim do cabeçalho
            //inicio dos detalhes
            html += '<div class="details"><div class="TypeandTime"><div class="duration"><p class="subtitle">Duração: </p> ' + '<p>' + planDetails[3] + 's</p></div></div> ';
            html += '<div class="TypeandTime"><div class="type"><p class="subtitle">Tipo: </p> <p>' + planDetails[2] + '</p></div></div>';
            html += '<div class="difrec"><div class="dif"><p class="subtitle" >Dificuldade: </p><p>' + planDetails[5] + '</p></div></div>';
            html += '<div class="difrec"><div class="rec"><p class="subtitle">Recompensa: </p><p>' + planDetails[6] + 'XP</p></div></div>';
            //html += '<div class="description">' + '<p>' + planDetails[1] + '</p></div></div>';
            //fim dos detalhes
            //Exercicios
            html += '</div> <div class="ContentEX"><h3 class="Exercicios">Exercícios</h3>';
            html += '<div class="menu"> ';
            for (var exerciseId in exercises) {
                var exerciseDetails = exercises[exerciseId];
                html += '<div class="ExContainer"><div class="ExImage"><img src=../' + exerciseDetails[5] + '> <h3 class="ExName">' + exerciseDetails[0] + '</h3></div ><div class="lowContent"><div class="type"><p class="ExType">Tipo: </p><p>' + exerciseDetails[3] + '</p></div> <div class="Diff"> <p class="ExType">Dificuldade: </p><p>' + exerciseDetails[4] + '</p></div></div ></div > '
                console.log('../' + exerciseDetails[2]);
                //html += 'div class="ExImage"><img src=../' + exerciseDetails[] + ' class="Eximg" ></div>';
            }
            html += '</div></div>';
            //fim dos exercicios
            html += '<div class="footer">';
            html += '<div class="footer-content">';
            html += '<img class="arrow-icon" src="../static/img/icon/arrow-232.svg" />';
            html += '<p>Voltar para os meus planos</p>';
            html += '</div>';
            html += '<div class="footer-content2">';
            html += '<button class="button"><span class="lable">Iniciar</span></button > ';
            html += '</div>';
            html += '</div>'
            container.append(html);
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
}

function moveMicrophone(top, left) {
    var microphone = document.getElementById('microphone');
    microphone.style.top = top;
    microphone.style.left = left;
}




function getPlanName_2(planNumber) {
    return fetch('/planotreino/' + planNumber)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            var planDetails = data[0];
            return planDetails[0]; // Return the plan's name
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });
}


function loadExercise_2(planNumber, count) {
    return fetch('/planotreino/' + planNumber)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Process the data and update the HTML content
            //document.getElementById('content').innerText = data.message;
            var container = $('#exercise');
            container.empty();
            var exercises = data[1]
            var totalExercises = exercises.length; // Get the total number of exercise
            var exerciseDetails = exercises[count]
            let videoFrame = document.getElementById('videoFrame');
            videoFrame.src = "";
            videoFrame.src = convertToEmbedUrl(exerciseDetails[2])
            var html = `<div class="videoContainer">
                            <div class="content">
                                <div class = "NameCont"><h3>${exerciseDetails[0]}</h3></div>
                                <div class="word"><span>Exercício:</span> <span id="counter">${count + 1}/${totalExercises}</span></div>
                                <div id = "descricao"> ${exerciseDetails[1]} </div>
                            </div>
                        </div>`;
            container.append(html);
            moveMicrophone('55%', '88.6%');
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });

}


function getPlanDuration_2(planNumber) {
    return fetch('/planotreino/' + planNumber)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            var planDetails = data[0];
            return planDetails[3];
        })
        .catch(error => {
            console.error('Fetch error:', error);
        });

}


function sendFinishPlan_2(elapsedTime, planNumber) {
    let data = {
        planNumber: planNumber,
        elapsedTime: elapsedTime,
    };
    console.log("debug:", data)

    // Make a POST request to the Flask route
    return fetch('/FinishSharedPlan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data) // Convert the data to a JSON string
    })
        .then(response => response.json())
        .then(data => console.log(data))
        .catch((error) => {
            console.error('Error:', error);
        });
}

function showAwardedBadges() {
    return fetch('/awardedBadges')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            var container = $('#badges');
            container.empty();
            var html = '<div class="titleend">Conquistas alcançadas:</div> <div class="achievements-container">';

            if (data.length == 0) {
                html += '<p>Nenhuma</p>';
            } else {
                for (var i = 0; i < data.length; i++) {
                    var badge = data[i];
                    var badgeId = Object.keys(badge)[0]; // Get the badge id
                    var badgeDetails = badge[badgeId]; // Get the badge details
                    
                    html += '<div class="flex-container">';
                    html += '<div class="box"><img src=' + badgeDetails[3] + ' alt="Your Image"></img></div>';
                    html += '<div class="box2" style="color: #92E3A9;"><p>' + badgeDetails[0] + '</p></div>';
                    html += '</div>';
                }
            }
            html += '</div>';

            container.append(html);
        })
        .catch(error => {
            console.error('Fetch error:', error);
            return Promise.reject(error);
        });
}

function showLevelProgress() {
    return fetch('/getlevelprogress')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            //console.log(data)

            var container = $('#pgbar');

            var html = `<div id="progress-bar">
                        <div id="progress"></div>
                    </div>
                    <div id="level-indicators">
                        <span id="current-level"></span>
                        <span id="next-level"></span>
                    </div>`;


            container.append(html);
            var user_xp = data.user_xp;
            var current_level = data.current_level;
            var next_level = data.next_level;

            var levelpercentage = (user_xp / next_level[1]) * 100;
            setProgress(levelpercentage);

            document.getElementById('current-level').textContent = `NÍVEL ${current_level[0]}`;
            document.getElementById('next-level').textContent = `NÍVEL ${next_level[0]}`;


        })
        .catch(error => {
            console.error('Fetch error:', error);
            return Promise.reject(error);
        });
}


function getplanxp(planNumber) {
    
        return fetch('/getplanxp/' + planNumber)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                //console.log(data);
                document.getElementById('Experience').innerHTML = "<div class='Experience'>Experiência Ganha: " + data + "</div>";
            })
            .catch(error => {
                console.error('Fetch error:', error);
                return Promise.reject(error);
            });
}

function setProgress(percentage) {
    var progressBar = document.getElementById('progress');
    progressBar.style.width = percentage + '%';
}

function formatTime(timeInMilliseconds) {
    let seconds = Math.floor((timeInMilliseconds / 1000) % 60);
    let minutes = Math.floor((timeInMilliseconds / (1000 * 60)) % 60);

    minutes = (minutes < 10) ? "0" + minutes : minutes;
    seconds = (seconds < 10) ? "0" + seconds : seconds;

    return minutes + ":" + seconds;
}

function convertToEmbedUrl(url) {
    let videoId = url.split('v=')[1];
    let embedUrl = 'https://www.youtube.com/embed/' + videoId + '?autoplay=1&mute=1&loop=1&playlist=' + videoId;
    return embedUrl;
}

function addfooter() {
    var container = $('#foot');
    container.empty();
    var html = `<div class="footer2">
                    <img class="arrow-icon" src="../static/img/icon/arrow-232.svg" />
                    <button class="button"><span class="lable">Avançar</span></button >
                </div>`;
    container.append(html);

}

function changeZIndex(z) {
    var element = document.getElementById('timerContainer');
    if (element) {
        element.style.zIndex = z;
    }
}

function addtimerimage() {
    var container = document.getElementById('timerContainer');
    if (container) {
        container.style.backgroundImage = "url('../static/img/watch1.png')";
    }
}

function removetimerimage() {
    var container = document.getElementById('timerContainer');
    if (container) {
        container.style.backgroundImage = "none";
    }
}


//mostrar stats no final do plano e caso user ganhe badges adquirir a devida badge!