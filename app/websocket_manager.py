from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from database import get_db
from routers import game as GameRouter
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        if len(self.active_connections) >= 2:
            await websocket.accept()
            await websocket.close(4000)
        else:
            await websocket.accept()
            self.active_connections.append(websocket)
            if len(self.active_connections) == 1:
                await websocket.send_json({
                    'init': True,
                    'status': 'None',
                    'player': '1',
                    'message': 'Waiting for another player',
                })
            else:
                await websocket.send_json({
                    'init': True,
                    'status': 'None',
                    'player': '2',
                    'message': '',
                })

                await self.active_connections[0].send_json({
                    'init': True,
                    'status': 'None',
                    'player': '1',
                    'message': 'Your turn!',
                })

                await self.broadcast({
                    'init': False,
                    'message': 'Load board',
                })

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message):
        for connection in self.active_connections:
            await connection.send_json(message)


boards = [None, None]
empty_boards = [[['~' for _ in range(10)] for _ in range(10)], [['~' for _ in range(10)] for _ in range(10)]]
current_player = "1"
status = "active"
game_id = None
manager = ConnectionManager()


def is_ship_destroyed(board, row, col):
    ship_cells = [(row, col)]
    directions = [
        (-1, 0), (1, 0),  # Проверка вертикально (вверх и вниз)
        (0, -1), (0, 1),  # Проверка горизонтально (влево и вправо)
    ]

    # Проверяем все направления от текущей клетки
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while 0 <= r < len(board) and 0 <= c < len(board[0]):
            if board[r][c] == "O":
                # Корабль не уничтожен, так как есть непоражённые клетки "ship"
                return False, []
            elif board[r][c] == "X":
                # Добавляем поражённые клетки к списку
                ship_cells.append((r, c))
                r += dr
                c += dc
            else:
                # Останавливаемся, если наткнулись на клетку, которая не является частью корабля
                break

    # Если весь корабль поражён
    return True, ship_cells


def update_surrounding_cells(board, ship_cells, empty_board):
    directions = [
        (-1, -1), (-1, 0), (-1, 1),  # Верхние диагональные и вертикальные
        (0, -1), (0, 1),  # Горизонтальные
        (1, -1), (1, 0), (1, 1),  # Нижние диагональные и вертикальные
    ]

    for row, col in ship_cells:
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < len(board) and 0 <= c < len(board[0]) and board[r][c] == "~":
                board[r][c] = "M"
                empty_board[r][c] = "M"


async def update_boards(player, row, col):
    global boards, current_player, empty_boards
    index = 0 if current_player == '2' else 1
    cell = boards[index][row][col]
    result = None
    if cell == '~':
        boards[index][row][col] = 'M'
        empty_boards[index][row][col] = 'M'
        result = "miss"
    elif cell == 'O':
        boards[index][row][col] = 'X'
        empty_boards[index][row][col] = 'X'
        result = "hit"
        destroyed, ship_cells = is_ship_destroyed(boards[index], row, col)
        if destroyed:
            result = "destroyed"
            update_surrounding_cells(boards[index], ship_cells, empty_boards[index])
    else:
        result = "incorrect move"
    if result == "miss":
        current_player = "2" if current_player == "1" else "1"

    # Проверка на завершение игры
    all_ships_sunk = all(
        boards[index][r][c] in ["M", "X"]
        for r in range(len(boards[index]))
        for c in range(len(boards[index][0]))
        if boards[index][r][c] != "~"
    )

    if all_ships_sunk:
        result = "game_over"

    return result


async def websocket_endpoint(websocket: WebSocket, client_id: int, db: Session = Depends(get_db)):
    global boards, current_player, status, game_id, empty_boards
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message["action"] == "game_created":
                game_id = message["data"]["id"]
                board1 = [list(row) for row in message["data"]["player_1_board"].splitlines()]
                board2 = [list(row) for row in message["data"]["player_2_board"].splitlines()]
                boards = [board1, board2]
                await manager.broadcast({
                        'init': True,
                        'status': 'get',
                        'message': 'boards',
                        'board1': {
                            "player": board1,
                            "opponent": empty_boards[0]
                        },
                        'board2': {
                            "player": board2,
                            "opponent": empty_boards[1]
                        }
                    })
            elif message["action"] == "make_move" and current_player == message["player"] and status == "active":
                res = await update_boards(current_player, message["row"], message["col"])
                if res == "incorrect move":
                    await manager.broadcast({
                        "init": True,
                        "status": "message",
                        "message": "Incorrect Move!"
                    })
                else:
                    await manager.broadcast({
                        "init": True,
                        "status": "message",
                        "message": f"Move ({message['row']}, {message['col']}): {res}"
                    })
                await manager.broadcast({
                    'init': True,
                    'status': 'get',
                    'message': 'boards',
                    'board1': {
                        "player": boards[0],
                        "opponent": empty_boards[1]
                    },
                    'board2': {
                        "player": boards[1],
                        "opponent": empty_boards[0]
                    }
                })
                if res == "game_over":
                    status = res
                    await manager.broadcast({
                        "init": True,
                        "status": "message",
                        "message": "Game is end!",
                    })
                    GameRouter.update_status(game_id=game_id, winner_id=int(current_player), db=db)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Unexpected error: {e}")


html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sea Battle Game</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 20px;
        }
        #game-container {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
        }
        #player-board, #opponent-board {
            display: grid;
            grid-template-columns: repeat(10, 30px);
            grid-template-rows: repeat(10, 30px);
            gap: 2px;
            margin-left: 20px;
        }
        .cell {
            width: 30px;
            height: 30px;
            background-color: #87CEEB;
            border: 1px solid #1E90FF;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
        }
        .cell.hit {
            background-color: red;
        }
        .cell.miss {
            background-color: white;
        }
        #message-box {
            margin-top: 20px;
            width: 300px;
            height: 150px;
            border: 1px solid #1E90FF;
            overflow-y: auto;
        }
        #message-box p {
            margin: 5px;
        }
        .ship {
            background-color: gray; /* Корабль */
        }
        .hit {
            background-color: red; /* Попадание */
        }
        .miss {
            background-color: white; /* Промах */
        }
    </style>
</head>
    <body>
        <h1>Sea Battle Game</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
            <div id="game-container">
            <div id="player-board"></div>
            <div id="opponent-board"></div>
        </div>

        <div id="message-box"></div>
        <script>
            function getCookie(name) {
                const cookieStr = document.cookie;
                console.log("document.cookie:", cookieStr); // Выводим все куки в консоль для диагностики
                const value = `; ${cookieStr}`;
                const parts = value.split(`; ${name}=`);
                if (parts.length === 2) return parts.pop().split(';').shift();
            }

            const  client_id = getCookie("id");
            console.log(client_id);
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            let player = null

            ws.onopen = () => {
                addMessage("Connected to server");
            };

            ws.onclose = function(e) {
                addMessage("Disconnected from server");
                console.log(e)
            };

            ws.onmessage = function(e) {
                response = JSON.parse(e.data)
                console.log("On message",response);
                if (response.init) {
                    if (response.status == "None") {
                        player = response.player;
                        addMessage(response.message);
                    } else if (response.status == "get") {
                        if (player == "1") {
                            updateBoard(response.board1);
                        } else if (player == "2") {
                            updateBoard(response.board2);
                        }
                    } else if (response.status == "message") {
                        addMessage(response.message);
                    }
                } else {
                    addMessage("Load desk")
                    if (player == "1") {
                    fetch("/game/create", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json"
                            },
                            body: JSON.stringify({
                                player_1_id: 1,
                                player_2_id: 2
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            console.log("Game created:", data); // Вывод результата в консоль
                            ws.send(JSON.stringify({ action: "game_created", data: data }));
                        })
                        .catch(error => console.error("Error:", error));
                    }
                }
            };

            function addMessage(message) {
                const messageBox = document.getElementById("message-box");
                const messageElement = document.createElement("p");
                messageElement.textContent = message;
                messageBox.appendChild(messageElement);
                messageBox.scrollTop = messageBox.scrollHeight;
            }

            function updateBoard(board) {
                const playerBoard = document.getElementById("player-board");
                const opponentBoard = document.getElementById("opponent-board");

                // Очистка предыдущего состояния
                playerBoard.innerHTML = '';
                opponentBoard.innerHTML = '';

                // Обновление доски игрока
                board.player.forEach((row, rowIndex) => {
                    row.forEach((cell, colIndex) => {
                        const cellDiv = document.createElement("div");
                        cellDiv.classList.add("cell");
                        if (cell === "O") {
                            cellDiv.classList.add("ship");
                        } else if (cell === "X") {
                            cellDiv.classList.add("hit");
                        } else if (cell === "M") {
                            cellDiv.classList.add("miss");
                        }
                        playerBoard.appendChild(cellDiv);
                    });
                });

                // Обновление доски соперника
                board.opponent.forEach((row, rowIndex) => {
                    row.forEach((cell, colIndex) => {
                        const cellDiv = document.createElement("div");
                        cellDiv.classList.add("cell");
                        if (cell === "O") {
                            cellDiv.classList.add("ship");
                        } else if (cell === "X") {
                            cellDiv.classList.add("hit");
                        } else if (cell === "M") {
                            cellDiv.classList.add("miss");
                        }
                        cellDiv.dataset.row = rowIndex;
                        cellDiv.dataset.col = colIndex;
                        cellDiv.addEventListener("click", () => {
                            handleCellClick(rowIndex, colIndex);
                        });
                        opponentBoard.appendChild(cellDiv);
                    });
                });
            }

            function handleCellClick(row, col) {
                ws.send(JSON.stringify({ action: "make_move", row: row, col: col, "player": player }));
            }
        </script>
    </body>
</html>
"""