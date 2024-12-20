INSERT INTO Types (TypeID, TypeName) VALUES
    (1, 'Питание'),
    (2, 'Патроны'),
    (3, 'Гранаты'),
    (4, 'Шлема'),
    (5, 'Бронежилеты');

INSERT INTO Supply (SupplyID, TypeID, SupName, SupDescription, StockQuantity, SupWeight) VALUES
    (1, 1, 'ИРП', 'Суточный рацион на одного бойца', 1000, 1),
    (2, 2, '7,62х49', 'Патрон промежуточный автоматный', 234, 1),
    (3, 3, 'РГД-1', 'Ручная противопехотная граната', 502, 2),
    (4, 4, 'ЗШ21', 'Шлем противоосколочный', 101, 4),
    (5, 5, 'БР21', 'Лёгкий бронежилет', 58, 20);

INSERT INTO Soldier (SoldierID, Fio, PasswordHash, SquadID,  Rank, BirthDate) VALUES
    (1, 'Иванов Иван Иванович', 'hash1', 1, 2, '2004-01-01'),
    (2, 'Иванов Василий Иванович', 'hash1', 1, 2, '2002-01-01'),
    (3, 'Иванов Владимир Иванович', 'hash1', 2, 2, '2001-01-01'),    
    (4, 'Иванов Сидор Иванович', 'hash1', 3, 2, '2000-01-01'),
    (5, 'Сидоров Иван Сидорович', 'hash2', 1, 1, '2001-02-01'),  
    (6, 'Сидоров Пётр Сидорович', 'hash2', 2, 1, '2002-02-01'),
    (7, 'Сидоров Виктор Сидорович', 'hash2', 3, 1, '2003-02-01'),
    (8, 'Сидоров Никита Сидорович', 'hash2', 3, 1, '2004-02-01'),
    (9, 'Петров Пётр Петрович', 'hash3', 1, 0, '2004-03-01');

INSERT INTO Request (ReqID, SoldierID, ReqDate, ReqStatus, TotalWeight) VALUES
    (1, 1, '2024-11-01', 'Обрабатывается', 15),
    (2, 2, '2024-11-02', 'Одобрен', 20),
    (3, 1, '2024-11-03', 'Отклонён', 5);

INSERT INTO ReqDet (ReqDetID, SupplyID, ReqID, Amount) VALUES
    (1, 1, 1, 5),
    (2, 3, 1, 5),
    (3, 5, 2, 1),
    (4, 1, 3, 5);

INSERT INTO Squad (SquadID, SquadComanderID) VALUES
    (1, 5),
    (2, 6),
    (3, 7);

INSERT INTO Reserve (ResID, SoldierID, SupplyID, Amount) VALUES
    (1, 1, 1, 1),
    (2, 2, 2, 2),
    (3, 2, 5, 1);

CREATE OR REPLACE FUNCTION check_stock() RETURNS TRIGGER AS $$
BEGIN
IF (SELECT NEW. reqstatus = 'Одобрен' FROM request AND SELECT stockquantity FROM supply WHERE supplyid = (SELECT supplyid FROM ReqDet WHERE ReqId = NEW. reqid) ‹ SELECT amount FROM ReqDet WHERE reqid = NEW. reqid)
THEN (RAISE EXCEPTION 'Недостаточное количество припаса на складе');
END IF;
RETURN NEW;
END;
$$ LANGUAGE plpgsq;

CREATE TRIGGER check_stock
BEFORE UPDATE ON Request
FOR EACH ROW
EXECUTE FUNCTION check_stock();

