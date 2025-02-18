CREATE TABLE Soldier (
    SoldierID SERIAL PRIMARY KEY,
    FIO VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    SquadID INT NOT NULL,
    Rank INT NOT NULL,
    BirthDate DATE NOT NULL
);

CREATE TABLE Squad (
    SquadID SERIAL PRIMARY KEY,
    SquadComanderID INT NOT NULL 
);

CREATE TABLE Supply (
    SupplyID SERIAL PRIMARY KEY,
    TypeID INT NOT NULL,
    SupName VARCHAR(100) NOT NULL,
    SupDescription TEXT,
    StockQuantity INT NOT NULL,
    SupWeight INT NOT NULL
);

CREATE TABLE Types (
    TypeID SERIAL PRIMARY KEY,
    TypeName VARCHAR(100) NOT NULL
);

CREATE TABLE ReqDet (
    ReqDetID SERIAL PRIMARY KEY,
    SupplyID INT NOT NULL,
    ReqID INT NOT NULL,
    Amount NUMERIC(10, 2) NOT NULL
);

CREATE TABLE Request (
    ReqID SERIAL PRIMARY KEY,
    SoldierID INT NOT NULL,
    ReqDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ReqStatus VARCHAR(50) DEFAULT 'Processing',
    TotalWeight INT NOT NULL
);

CREATE TABLE Reserve (
    ResID SERIAL PRIMARY KEY,
    SoldierID INT NOT NULL,
    SupplyID INT NOT NULL,
    Amount INT NOT NULL
);

CREATE UNIQUE INDEX reserve_soldierid_supplyid_unique 
ON reserve (soldierid, supplyid);



CREATE VIEW ReqDetSupplyView AS
SELECT 
    r.ReqID,
    s.SupName,
    r.Amount
FROM 
    ReqDet r
JOIN 
    Supply s ON r.SupplyID = s.SupplyID;



CREATE VIEW ResSupplyView AS
SELECT 
    r.ResID,
    s.SupName,
    r.Amount
FROM 
    Reserve r
JOIN 
    Supply s ON r.SupplyID = s.SupplyID;



CREATE OR REPLACE FUNCTION check_stock() RETURNS TRIGGER AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN
        SELECT supplyid, amount FROM ReqDet WHERE ReqId = NEW.reqid
    LOOP
        IF ((SELECT stockquantity FROM supply WHERE supplyid = rec.supplyid) < rec.amount) 
        THEN RAISE EXCEPTION 'Недостаточно припасов!';
        END IF;
    END LOOP;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE TRIGGER change_stock
BEFORE UPDATE ON Request
FOR EACH ROW
WHEN (NEW. reqstatus = 'Одобрен')
EXECUTE FUNCTION check_stock();




CREATE OR REPLACE PROCEDURE ReqApply(nreq INT)
LANGUAGE plpgsql AS $$
DECLARE
    rec RECORD;
    soldier_id INT;
BEGIN
    SELECT soldierid INTO soldier_id
    FROM request
    WHERE reqid = nreq;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Запись с reqid = % не найдена', nreq;
    END IF;
    FOR rec IN
        SELECT supplyid, amount FROM reqdet WHERE reqid = nreq
    LOOP
        UPDATE supply
        SET stockquantity = stockquantity - rec.amount
        WHERE supplyid = rec.supplyid;
        INSERT INTO reserve (soldierid, supplyid, amount)
        VALUES (soldier_id, rec.supplyid, rec.amount)
        ON CONFLICT (soldierid, supplyid) DO UPDATE
        SET amount = reserve.amount + EXCLUDED.amount;
    END LOOP;
END;
$$;