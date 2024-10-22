if (board) { //loading screen
    (()=>{    var tab=document.getElementById("loadtab");
    var arr=[];
    for (y=0; y<8; y++) {
	var line=document.createElement("tr");
	tab.appendChild(line);
	var l=[];
        for (x=0; x<8; x++) {
	    var pt=document.createElement("td");
	    var pti=document.createElement("div");
	    pti.className="dot";
	    pt.appendChild(pti);
	    line.appendChild(pt);
	    l.push(pti);
	}
	arr.push(l);
    }

    var snake = [[2,2],[3,2],[4,2],[5,2],[5,3],[5,4],[5,5],
		 [4,5],[3,5],[2,5],[2,4],[2,3]];
    var snakelen = 10;
    var pos = 0;
    function redraw() {
	for (var i=0; i<12; i++) {
	    var cl = ((i+pos)%12==0)?"head":
		((i+pos)%12<snakelen)?"tail":"dot";
	    arr[snake[i][0]][snake[i][1]].className=cl;
	}
    }
    window.setInterval(()=>{pos++;redraw()},600);
//    var lenel=document.getElementById("snakelen");
//    lenel.addEventListener("change", ()=>snakelen=lenel.value);
    redraw();
     })();
}

if (!board) {
    if (window.location.hash.length>1) { 
	var player=parseInt(window.location.hash.replace(/^./,""));
    } else {
	var player = prompt("player? (0-3)");
    }
    var click = new Audio("START.WAV");
}
rotate = player%4;

var ws;
function gebi(id) { return document.getElementById(id); }
var el = gebi("log");
var statel = gebi("status");
var score;
var q=[ 'Oof! Ran into the edge!',
      'Ouch! Ran into yourself!',
      'Eek! Ran into another snake!',
      'Yum! Ate a glowy thing.',
      'Nice! Absorbed a rotting corpse.',
    ];

var states = [ 'Ready', 'Alive', 'Dead', 'Dead' ];
var deaths = [
    null,
    "ran into the edge.",
    "hit a wall.",
    "couldn't keep it together.",
    "crashed.",
    "bit off more than they could chew.",
];

var deaths2 = [
    null,
    "ran into the edge.",
    "hit a wall.",
    "ran into yourself.",
    "crashed.",
    "ate your own tail.",
];

//var board = true; // are we the big status board or a player?
function status() {
    if (connecting) {
	//draw modal spinner
    }
}

function status(l) {
    if (!board) {
	statel.innerHTML=l;
    }
}

function logto(el,l) {
    var line=document.createElement("div");
    line.innerHTML=l;
    el.appendChild(line);
    line.scrollIntoView({ behavior: 'smooth' });
    //window.scrollTo(0,document.body.scrollHeight);
}

function log(l) {
    //console.log(l);
    //el.innerHTML="<br>"+l;
    if (board) {
	logto(gebi("log"),l);
	logto(gebi("log2"),l);
    }
}
function send(o) {
    ws.send(JSON.stringify(o));
}
function mainstart() {
	gebi("mainpage").style.display="flex";
	gebi("startpage").style.display="none";
    for (var i=0;i<27;i++) {
	//log("test log entry "+i);
	log(" ");
    }
}
function exiting() {
	gebi("mainpage").style.display="none";
	gebi("startpage").style.display="none";
	gebi("blackpage").style.display="block";
}

function starting() {
}

function connected() {
    if (!board) {
	send({player:player});
    } else {
	mainstart();
    }
    status("connected");
}
function reconnect() {
    status("reconnecting");
    window.setTimeout(wsstart,300);
}

var players=[], scores=[];
function fmtpl(pl) {
    var col = players[pl].col;
    var colname = players[pl].colname;
    return "<span style='color:"+col+"'>"+colname+"</span>";
}

function onmsg(e) {
    m=JSON.parse(e.data);
    console.log(m);
    switch (m.type) {
    case 'hisc':
	hisc = m.score;
	hiname = m.name;
	hitime = m.time;
	hicol = m.col;
	if (board) {
	    var s="High score <span id=hi>"+hisc+"</span>";//<br>";
	    if (hiname) {
		s += " by <span id=hiname style='color:rgb("+hicol+")'>"+hiname+"</span>";
	    }
	    //s += " at "+hitime;
	    gebi("hisc").innerHTML=s;
	}
	break;
    case 'gothi':
	var sc = m.score;
	var name=prompt("You got a high score! Enter your name (if you like)");
	send({hiscname:name,hisc:sc});
	break;
    case 'exiting':
	exiting();
	break;
    case 'dead':
	//log("player "+m.player+" died with reason "+m.reason);
	//log(fmtpl(m.player)+" died with reason "+m.reason);
	if (board) {
	    log(fmtpl(m.player)+" "+deaths[m.reason]);
	} else {
	    //status("You "+deaths2[m.reason]);
	}
	break;
    case 'spawn':
	//log("player "+m.player+" spawned");
	var pl = m.player;
	var col = players[pl].col;
	var colname = players[pl].colname;
	log("Go "+fmtpl(pl)+"!");
	break;
    case 'players':
	players = m.players;
	if (!board) {
	    status("You are "+players[player].colname);
	    //status("You are "+fmtpl(player));
	    //gebi("gradient").style.background="linear-gradient(white,"+players[player].col+")";
	    gebi("body2").style.background=players[player].col;
	    //document.body.style.background=players[player].col;
	}
	break;
    case 'scores':
	scores = m.players;
	if (board) {
	    // draw all scores
	    drawscores(gebi("scores"));
	    drawscores(gebi("scores2"));
	} else {
	    //gebi("score").innerHTML = "Score: "+scores[player].score;
	    switch (scores[player].state) {
	    case 1: // alive
		if (scores[player].score) {
		    status("Score: "+scores[player].score);
		} else {
		    status("You are "+players[player].colname);
		    //status("You are "+fmtpl(player));
		}
		break;
	    case 0: // ready
		status("Ready!");
		break;
	    default:
		if (scores && scores[player] && scores[player].score) {
		    status("Game over<br>You scored "+scores[player].score);
		} else {
		    status("Game over");
		}
		break;
	    }
	}
	break;
    case 'newhi':
	var pl = m.player;
	log(fmtpl(pl)+" got a high score!");
	break;
    }
}

function drawscores(e) {
    var s="<tr><th></th><th>Score</th><th>Time</th></tr>";
    for (var i=0;i<scores.length;i++) {
	if (scores[i] /*&& scores[i].state is OK */) {
	    console.log(scores[i]);
	    var state="<td>"+states[scores[i].state]+"</td>";
	    if (scores[i].state==1/*ALIVE*/) {
		var ss=scores[i].for;
		var mm=(ss/60)|0;
		ss-=mm*60;
		ss=((ss>9)?'':'0')+ss;
		state = "<td style='text-align:right'>"+mm+":"+ss+"</td>";
	    }
	    s += "<tr><td>"+fmtpl(i)+"</td><td align=center>"+scores[i].score+"</td>"+state+"</tr>";
	}
	    }
    e.innerHTML = s;
}

function wsstart() {
    ws = new WebSocket("ws://"+window.location.hostname+":27681/");
    ws.onopen = connected;
    ws.onclose = reconnect;
    //ws.onerror = function () {log("error")};
    ws.onmessage = onmsg;
}

if (!board) {
    function sendkey(k) {
	log("sent "+k);
	if (k<4) {k = [0,2,1,3][([0,2,1,3][k]+rotate)%4];}
	send({key:k});
	try {window.navigator.vibrate && window.navigator.vibrate(10);}catch (e){}
	try {click.play();}catch (e){}
    }
    window.onkeydown = function(e) {
	if (e.key=='r') {rotate=(rotate+1)%4;return;}
	var k=keys[e.key];
	if (k!==undefined)
            sendkey(k);
    }
    
    for (var i=0;i<6;i++) {
	gebi("b"+i).addEventListener('touchstart', ((i)=>(()=>sendkey(i)))(i));
	gebi("b"+i).addEventListener('click', ((i)=>(()=>sendkey(i)))(i));
    }
//    keys = { a:0, d:1, w:2, s:3, q:4, e:5 };
    keys = { a:0, d:1, w:4, s:5, q:2, e:3 };

}

wsstart();
function dofs() {
    if (document.body.requestFullScreen)
	document.body.requestFullScreen();
    else if (document.body.requestFullscreen)
	document.body.requestFullscreen();
    else if (document.body.mozRequestFullScreen)
	document.body.mozRequestFullScreen();
    else alert("no");
    gebi("fs").style.display="none";
}

if (!board)
    gebi("fs").onclick = dofs;
    
//setInterval(()=>log(Math.random()),1000);
