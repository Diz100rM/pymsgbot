# PyMsgBOT
Python quote bot for Telegram

Всем привет. Этот бот создан для сохранения цитат одного или нескольких человек в телеграмм (чем-то похоже на bash.im)
Для того чтобы установить и запустить бота вам нужно выполнить несколько шагов.




 1)git clone https://github.com/Diz100rM/pymsgbot.git

 2)cd pymsgbot

 3)pip install -r requirements.txt

 4)python main.py




Для корректной работы вам нужно создать 2 базы данных этими SQL коммандами:



 1) CREATE DATABASE pymsgbot;  (если вы планируете создать отдельную базу данных)

 2) CREATE TABLE quotes(
    id INT NOT NULL AUTO_INCREMENT,
    date VARCHAR(20),
    owner VARCHAR(200),
    quote VARCHAR(2000),
    media_id VARCHAR(1000),
    PRIMARY KEY(id)
);

 3) CREATE TABLE votes (
    quote_id int,
    user_Id int,
    rate tinyint,
    UNIQUE KEY votes_quote_user_unique (quote_id, user_id)
 );



После этого укажите данные БД в файл config.py

Также укажите токен бота который вы можете получить у @BotFather

Отключите Privacy Mode в настройках бота

Бот готов к работе!



Комманды для взаимодействия:

/save (Ответьте на сообщение которое вы хотите сохранить и оно будет добавлено в базу данных, с присвоенным ему ID)

/quote id (Показывает сообщение с указанным ID, без ID не работает)

/delete id (Удаляет цитату с указанным ID, без ID не работает)




Для сохранения нескольких сообщений выделите необходимые и отправьте боту в личную переписку. В течении 2ух секунд цитата будет сохранена!


--- Информация может дополнятся ---
