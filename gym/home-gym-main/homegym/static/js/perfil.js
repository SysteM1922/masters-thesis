function showStreak() {
    fetch('/streak')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            var streak = data;
            var container = $('#streak');
            container.empty();

            var html = '<div class="streak" >Streak ' + streak + ' <img src="../static/img/badge4image.jpeg" alt="Icon" style="width: 20px; height: 20px;"></div>';

            container.append(html);
        })
        .catch(error => {
            console.error('Fetch error:', error);
            return Promise.reject(error);
        });
}

function getBadges() {
    Promise.all([
        fetch('/userBadges'),
        fetch('/allBadges')
    ])
        .then(async ([res1, res2]) => {
            if (!res1.ok) {
                throw new Error(`HTTP error! Status: ${res1.status}`);
            }
            if (!res2.ok) {
                throw new Error(`HTTP error! Status: ${res2.status}`);
            }
            return Promise.all([res1.json(), res2.json()]);
        })
        .then(([userBadges, allBadges]) => {
            console.log(userBadges, allBadges);
            var container = $('#content');
            container.empty();

            var html = '<p class="stats2" style="margin-top:-8vh">SUAS CONQUISTAS</p>';
            html += '<div class="card-container">';

            if (userBadges.length === 0) {
                html += '<p>Ainda não ganhou nenhuma conquista.</p>';
            } else {
                for (badge of userBadges) {
                    html += '<div class="card" style="margin-top:-1.5vh" >';
                    html += '<img src="' + badge[3] + '" alt="Avatar">';
                    html += '<div class="container">'
                    //html += '<div class="text-stats">' + badge[0] + ' </div>';
                    html += '<div class="text-stats">' + badge[1] + ' </div>';
                    html += '</div>';
                    html += '</div>';
                }
            }

            html += '</div>';

            var badgesToWin = allBadges.filter(badge => !userBadges.some(userBadge => userBadge[0] === badge[0]));

            // Display the badges that the user doesn't have yet
            html += '<p class="stats2">CONQUISTAS POR GANHAR</p>';
            html += '<div class="card-container2">';
            if (badgesToWin.length === 0) {
                html += '<p>Não tem mais badges para ganhar.</p>'; // Replace with your message
            } else {
                for (badge of badgesToWin) {
                    html += '<div class="card">';
                    html += '<img src="' + badge[3] + '" alt="Avatar" style=" filter: grayscale(100%);">';
                    html += '<div class="container">'
                    //html += '<div class="text-stats">' + badge[0] + ' </div>';
                    html += '<div class="text-stats">' + badge[1] + ' </div>';
                    html += '</div>';
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

function showinfo() {
    return fetch('/info')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            var container = $('#content');
            container.empty();
            var full_name = data.full_name;
            var measurements = data.measurements;
            var age = data.age;
            var register_date = data.register_date

            var html = '<div class="parent-div">'; // Start of parent div
            html += '<div class="left-side2">';
            html += '<div class="stats2">';
            html += '<div class="titleprg">Nome</div>';
            html += '<div class="titlevalues">' + full_name + '</div>';
            html += '<div class="titleprg">Idade</div>';
            html += '<div class="titlevalues">' + age + '</div>';
            html += '<div class="titleprg">Data de Inicio</div>';
            html += '<div class="titlevalues">' + register_date + '</div>';
            html += '</div>'; // Closing tag for 'stats2' div
            html += '</div>'; // Closing tag for 'left-side2' div
            html += '<div class="right-side2">';
            html += '<div class="stats2">';
            html += '<div class="stat-block">';
            html += '<div class="titleprg">Altura</div>';
            html += '<div class="titlevalues">' + measurements[2] + ' cm</div>'; // Adds 'cm' for centimeters
            html += '</div>';
            html += '<div class="stat-block">';
            html += '<div class="titleprg">Peso</div>';
            html += '<div class="titlevalues">' + measurements[3] + ' kg</div>'; // Adds 'kg' for kilograms
            html += '</div>';
            html += '<div class="stat-block">';
            html += '<div class="titleprg">IMC</div>';
            html += '<div class="titlevalues">' + measurements[6] + ' kg/m²</div>'; // IMC is unitless
            html += '</div>';
            html += '</div>'; // Closing tag for 'stats2' div
            html += '</div>'; // Closing tag for 'right-side2' div
            html += '</div>'; // End of parent div
            container.append(html);
        })
        .catch(error => {
            console.error('Fetch error:', error);
            return Promise.reject(error);
        });

}

function getProgress() {
    return fetch('/progress')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            var container = $('#content');
            container.empty();

            var plansDone = data.plans_done;
            var exsDone = data.exs_done;
            var avgTime = data.avg_time;
            var total_time = data.total_time;

            var html = '<div class="stats3">';
            html += '<div class ="TempoTreino"><div class="titleprg">Total de tempo a treinar</div>';
            html += '<div class="title_group1"> <div class="titlevalues_animated_1">' + total_time + '</div><span id="timedesign">min</span></div></div>';
            html += '<div class="PlanosFeitos"><div class="titleprg">Planos de treino realizados</div>';
            html += '<div class="titlevalues">' + plansDone + '</div></div>';
            html += '<div class="TempoMedio"><div class="titleprg">Tempo médio por treino</div>';
            html += '<div class="title_group1"> <div class="titlevalues_animated_2">' + avgTime + '</div> <span id="timedesign">seg</span></div></div></div>';

            html += `<div id="Progress-bar">
                        <div id="progress"></div>
                    <span id="current-level"></span>
                    <div id="level-indicators">
                        
                    </div>`;

            container.append(html);


            animateNumber($('.titlevalues_animated_1'), total_time);
            animateNumber($('.titlevalues'), plansDone);
            animateNumber($('.titlevalues_animated_2'), avgTime);

            function animateNumber(element, newValue) {
                $({ value: 0 }).animate({ value: newValue }, {
                    duration: 1000,
                    easing: 'swing',
                    step: function () {

                        var formattedValue = this.value;
                        if (element.hasClass('titlevalues_animated_1')) {
                            formattedValue = this.value.toFixed(2);
                        } else if (element.hasClass('titlevalues_animated_2')) {
                            formattedValue = this.value.toFixed(0);
                        }
                        else {
                            formattedValue = this.value.toFixed(0);
                        }
                        element.text(formattedValue);
                    }
                });
            }

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
            console.log(data)
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

function setProgress(percentage) {
    var progressBar = document.getElementById('progress');
    progressBar.style.width = percentage + '%';
    console.log(percentage);
}

function showContent() {
    var html = `
        <div class="main-group">
            <div class="dashboard-content">
                <div class="progresso_sq">
                    <div class="title_sq">Progresso</div>
                </div>
                <div class="info_sq">
                    <div class="title_sq">Informações</div>
                </div>
                <div class="conquistas_sq">
                    <div class="title_sq">Conquistas</div>
                </div>
            </div>
        </div>
        <div class="footer-content">
            <p>Voltar para o menu</p>
            <img class="arrow-icon" src="../static/img/icon/arrow-232.svg" />
        </div>
    `;

    $('#content').html(html);
}
