const expressionEl = document.querySelector("#expression");
const resultEl = document.querySelector("#result");
const historyList = document.querySelector("#history-list");
const clearHistoryButton = document.querySelector("#clear-history");

let expression = "";
let lastResult = "";
let memory = 0;
let history = JSON.parse(localStorage.getItem("calculator-history") || "[]");

const render = () => {
    expressionEl.textContent = expression || "0";
    renderHistory();
};

const renderHistory = () => {
    historyList.innerHTML = "";

    if (!history.length) {
        const empty = document.createElement("li");
        empty.className = "empty-history";
        empty.textContent = "No calculations yet";
        historyList.appendChild(empty);
        return;
    }

    history.slice(0, 8).forEach((item) => {
        const row = document.createElement("li");
        const expressionLine = document.createElement("div");
        const resultLine = document.createElement("div");

        expressionLine.className = "history-expression";
        resultLine.className = "history-result";
        expressionLine.textContent = item.expression;
        resultLine.textContent = item.result;

        row.append(expressionLine, resultLine);
        row.addEventListener("click", () => {
            expression = item.result;
            resultEl.textContent = "Loaded";
            resultEl.classList.remove("error");
            render();
        });

        historyList.appendChild(row);
    });
};

const saveHistory = () => {
    localStorage.setItem("calculator-history", JSON.stringify(history.slice(0, 20)));
};

const appendValue = (value) => {
    if (resultEl.classList.contains("error")) {
        resultEl.classList.remove("error");
        resultEl.textContent = "Ready";
    }

    if (!expression && ["+", "×", "÷", "%", "^"].includes(value)) {
        expression = lastResult || "";
    }

    expression += value;
    render();
};

const calculate = async () => {
    const currentExpression = expression;

    try {
        const response = await fetch("/api/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ expression: currentExpression }),
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not calculate.");
        }

        lastResult = data.result;
        resultEl.textContent = data.result;
        resultEl.classList.remove("error");

        history.unshift({ expression: currentExpression, result: data.result });
        saveHistory();
        renderHistory();
    } catch (error) {
        resultEl.textContent = error.message;
        resultEl.classList.add("error");
    }
};

const clearAll = () => {
    expression = "";
    resultEl.textContent = "Ready";
    resultEl.classList.remove("error");
    render();
};

const backspace = () => {
    expression = expression.slice(0, -1);
    render();
};

const applyPercent = () => {
    const match = expression.match(/(-?\d+(?:\.\d+)?)$/);
    if (!match) return;

    const percentValue = String(Number(match[1]) / 100);
    expression = expression.slice(0, match.index) + percentValue;
    render();
};

const toNumber = (value) => {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
};

const currentValue = () => toNumber(lastResult || expression);

const handleAction = (action) => {
    if (action === "clear") clearAll();
    if (action === "backspace") backspace();
    if (action === "calculate") calculate();
    if (action === "percent") applyPercent();
    if (action === "memory-clear") memory = 0;
    if (action === "memory-recall") appendValue(String(memory));
    if (action === "memory-add") memory += currentValue();
    if (action === "memory-subtract") memory -= currentValue();
};

document.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;

    const { value, action } = button.dataset;
    if (value) appendValue(value);
    if (action) handleAction(action);
});

document.addEventListener("keydown", (event) => {
    const keyMap = {
        "*": "×",
        "/": "÷",
        Enter: "calculate",
        Escape: "clear",
        Backspace: "backspace",
    };

    if (/^[0-9.+\-()]$/.test(event.key)) {
        event.preventDefault();
        appendValue(event.key);
        return;
    }

    if (event.key === "%") {
        event.preventDefault();
        applyPercent();
        return;
    }

    if (event.key === "^") {
        event.preventDefault();
        appendValue("^");
        return;
    }

    const mapped = keyMap[event.key];
    if (!mapped) return;

    event.preventDefault();
    if (["calculate", "clear", "backspace"].includes(mapped)) {
        handleAction(mapped);
    } else {
        appendValue(mapped);
    }
});

clearHistoryButton.addEventListener("click", () => {
    history = [];
    saveHistory();
    renderHistory();
});

render();
