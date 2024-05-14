
topic = '';
question = '';
allBlanks = [];
choices = [];
code = '';
currentBlank = 0;

$(document).ready(function() {
    // Function to get code
    if (window.location.pathname.includes('/question')) {
        var questionID = document.getElementById("questionID").value;
        console.log(questionID);

        $.ajax({
            url: '/get_question/'+questionID,
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                console.log(response);
                // let questionObject = JSON.parse(response);
                topic = response.topic;
                $('#question-topic').html(topic);

                question = response.question;
                $('#question-text').html(question);

                allBlanks = response.allBlanks;
                choices = response.choices;

                code = response.code;

                // adding blanks
                for (let i = allBlanks.length - 1; i >= 0; i--) {
                    var blankColor = 'border-indigo-600';
                    if (i == currentBlank) {
                        blankColor = 'border-green-600';
                    }
                    
                    var width = 120;
                    if(choices[allBlanks[i][2]].length > 10) {
                        width = 200;
                    }
                    var thisBlank = '</pre><div style="height: 50px; width: '+width+'px" class="inline-block border-2 border-dashed '+blankColor+' rounded-lg mx-2 p-1" id="blankDiv-'+i+'"> <button style="margin: 0; height: 100%; width: 100%;" class="bg-gray-300 rounded-lg hidden" id="blankButton-'+i+'" onclick="handleBlankButtonClick(this.id)">' + allBlanks[i][3] + '</button></div><pre>';
                
                    code = insertBlank(code, allBlanks[i][0], allBlanks[i][1] + 1, thisBlank);
                }
                
                let lines = code.split('\n');

                // adding p tags to start and end of every line
                code = '';
                for (let i=0; i<lines.length; i++) {
                    lines[i] = '<div class="flex items-center my-2"><pre>'+lines[i]+'</pre></div>';
                    code += lines[i];
                }
                
                console.log(lines);
                // replacing 4 spaces with <br> and  \t 
                // code = code.replace(/\n/g, "<br>");
                // code = code.replace(/ {4}/g, "\t");
                
                $("#loading-div").addClass("hidden");
                $("#question-div").removeClass("hidden");
                $('#question-code').html(code);
                // console.log(response);

                // adding choices
                var choicesHTML = '';
                for (let i=0; i<choices.length; i++) {
                    choicesHTML += '<button style="height: 42px; " class="bg-gray-300 rounded-lg mr-2 px-2" id="choice-'+i+'" onclick="handleChoiceClick(this.id)">'+choices[i]+'</button>';
                }
                $('#question-choices').html(choicesHTML);
            },
            error: function(error) {
                console.log('Error:', error);
            }
        });

        function insertBlank(str, startIndex, endIndex, replacement) {
            // Get the part before the start index
            let start = str.substring(0, startIndex);
            
            // Get the part after the end index
            let end = str.substring(endIndex, str.length);
            
            // Combine the parts with the replacement in the middle
            return start + replacement + end;
        }
    }
});

function handleBlankButtonClick(blankButtonId) {
    console.log(blankButtonId);
    console.log("Current topic:", topic);

    $("#"+blankButtonId).addClass("hidden");
    
    var blankNumber = getNumberFromId(blankButtonId);
    var choiceId = allBlanks[blankNumber][3];
    allBlanks[blankNumber][3] = -1;

    $("#blankDiv-"+currentBlank).removeClass("border-green-600");
    $("#blankDiv-"+currentBlank).addClass("border-indigo-600");
    $("#blankDiv-"+blankNumber).removeClass("border-indigo-600");
    $("#blankDiv-"+blankNumber).addClass("border-green-600");
    currentBlank = blankNumber;

    $("#choice-"+choiceId).removeClass("hidden");
}

function handleChoiceClick(choiceId) {
    console.log(choiceId);

    if (allBlanks[currentBlank][3] != -1) return; // the blank is already full

    $("#"+choiceId).addClass("hidden");
    var choiceNumber = getNumberFromId(choiceId);
    var choice = choices[choiceNumber];
    console.log(currentBlank);
    console.log(choice);
    $("#blankButton-"+currentBlank).removeClass("hidden");
    $("#blankButton-"+currentBlank).html(choice);

    allBlanks[currentBlank][3] = choiceNumber;

    $("#blankDiv-"+currentBlank).removeClass("border-green-600");
    $("#blankDiv-"+currentBlank).addClass("border-indigo-600");
    currentBlank = (currentBlank+1)%allBlanks.length;
    $("#blankDiv-"+currentBlank).removeClass("border-indigo-600");
    $("#blankDiv-"+currentBlank).addClass("border-green-600");
}

function getNumberFromId(id) {
    // Use a regular expression to find the digits at the end of the string
    const result = /(\d+)$/.exec(id);
    return result ? parseInt(result[1], 10) : null;
}

function runCode() {
    var isCorrect = true;
    for (let i = 0; i<allBlanks.length; i++) {
        if (allBlanks[i][2] != allBlanks[i][3]) {
            isCorrect = false;
            break;
        }
    }

    if (isCorrect) {
        // alert("Code is correct!");
        openModal(true);
    } else {
        // alert("Code is incorrect");
        openModal(false);
    }
}

function openModal(isCodeCorrect) {
    document.getElementById('my-modal').style.display = 'block';
    if (isCodeCorrect) {
        $("#result-modal").text("Your code is correct!");
    } else {
        $("#result-modal").text("Your code is incorrect!");
    }
}

function closeModal() {
    document.getElementById('my-modal').style.display = 'none';
}