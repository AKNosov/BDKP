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



CREATE OR REPLACE FUNCTION check_stock(nreqid INT) RETURNS VOID AS $$
BEGIN
IF ((SELECT stockquantity FROM supply WHERE supplyid = (SELECT supplyid FROM ReqDet WHERE ReqId = nreqid)) < (SELECT amount FROM ReqDet WHERE reqid = nreqid))
THEN RAISE EXCEPTION 'Недостаточное количество припаса на складе';
END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE PROCEDURE ReqApply()
LANGUAGE plpgsql AS $$
DECLARE rec RECORD;
BEGIN
    EXECUTE check_stock(NEW. reqid);
    FOR rec IN
        SELECT supplyid, amount FROM reqdet WHERE reqid = NEW. reqid
    LOOP
        UPDATE supply
        SET stockquantity = stockquantity - rec.amount
        WHERE supplyid = rec.supplyid;
        UPDATE reserve
        SET amount = amount + rec.amount
        WHERE soldierid = (SELECT soldierid FROM request WHERE reqid = NEW. reqid)
          AND supplyid = rec.supplyid;
    END LOOP;
END;
$$;





CREATE OR REPLACE TRIGGER change_stock
BEFORE UPDATE ON Request
FOR EACH ROW
WHEN (NEW. reqstatus = 'Одобрен')
EXECUTE PROCEDURE ReqApply();




