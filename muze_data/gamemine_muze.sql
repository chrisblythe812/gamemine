CREATE TABLE Association (
  AssociationID varchar(100) NOT NULL,
  ID_1 varchar(100) NOT NULL,
  ID_2 varchar(100) NOT NULL,
  AssociationType varchar(100) NOT NULL,
  Weight float NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_Association_AssociationID ON Association USING btree(AssociationID);
CREATE INDEX Index_Association_ID_1 ON Association USING btree(ID_1);
CREATE INDEX Index_Association_ID_2 ON Association USING btree(ID_2);


CREATE TABLE Attribute (
  AttributeID varchar(100) NOT NULL,
  Type varchar(1) NOT NULL,
  PropertyTypeID varchar(100) NOT NULL,
  Attribute varchar(255) NOT NULL,
  KeyAttribute varchar(255) NOT NULL,
  Description varchar(255) NOT NULL,
  Format varchar(255) NOT NULL,
  Range varchar(255) NOT NULL,
  EnumeratedValues varchar(255) NOT NULL,
  n_Links int NOT NULL,
  n_Objects int NOT NULL,
  n_Values int NOT NULL,
  n_Children int NOT NULL,
  n_Parents int NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_Attribute_AttributeID ON Attribute USING btree(AttributeID);


CREATE TABLE AttributeAssociation (
  AttributeAssociationID varchar(100) NOT NULL,
  AttributeID_1 varchar(100) NOT NULL,
  AttributeID_2 varchar(100) NOT NULL,
  AssociationType varchar(100) NOT NULL,
  GroupID varchar(100) NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_AttributeAssociation_AttributeAssociationID ON AttributeAssociation USING btree(AttributeAssociationID);
CREATE INDEX Index_AttributeAssociation_AttributeID_2 ON AttributeAssociation USING btree(AttributeID_2);


CREATE TABLE AttributeLink (
  AttributeLinkID varchar(100) NOT NULL,
  ObjectID varchar(100) NOT NULL,
  PropertyAttributeID varchar(100) NOT NULL,
  ValueAttributeID varchar(100) NOT NULL,
  Value text NOT NULL,
  Weight float NOT NULL,
  Rank float NOT NULL,
  p_BaseObjectID varchar(100) NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_AttributeLink_AttributeLinkID ON AttributeLink USING btree(AttributeLinkID);
CREATE INDEX Index_AttributeLink_ObjectID ON AttributeLink USING btree(ObjectID);


CREATE TABLE Clip (
  ClipID varchar(100) NOT NULL,
  FileName varchar(255) NOT NULL,
  Width int NOT NULL,
  Height int NOT NULL,
  MimeType varchar(100) NOT NULL,
  FileSize int NOT NULL,
  Length int NOT NULL,
  SetID int NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_Clip_ClipID ON Clip USING btree(ClipID);


CREATE TABLE ClipLink (
  ClipLinkID varchar(100) NOT NULL,
  MainObjectID varchar(100) NOT NULL,
  ClipID varchar(100) NOT NULL,
  ClassificationAttributeID varchar(100) NOT NULL,
  PositionAttributeID varchar(100) NOT NULL,
  Caption varchar(255) NOT NULL,
  SortOrder int NOT NULL,
  PublishDate date NOT NULL,
  p_FileName varchar(255) NOT NULL,
  p_Width int NOT NULL,
  p_Height int NOT NULL,
  p_MimeType varchar(100) NOT NULL,
  p_FileSize int NOT NULL,
  p_Ratio float NOT NULL,
  p_Length int NOT NULL,
  p_SetID int NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_ClipLink_ClipLinkID ON ClipLink USING btree(ClipLinkID);
CREATE INDEX Index_ClipLink_MainObjectID ON ClipLink USING btree(MainObjectID);


CREATE TABLE Document (
  DocumentID varchar(100) NOT NULL,
  TypeAttributeID varchar(100) NOT NULL,
  Title varchar(255) NOT NULL,
  FullText text NOT NULL,
  URL text NOT NULL,
  Format varchar(1) NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_Document_DocumentID ON Document USING btree(DocumentID);


CREATE TABLE Image (
  ImageID varchar(100) NOT NULL,
  FileName varchar(255) NOT NULL,
  Width int NOT NULL,
  Height int NOT NULL,
  MimeType varchar(100) NOT NULL,
  FileSize int NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_Image_ImageID ON Image USING btree(ImageID);


CREATE TABLE ImageLink (
  ImageLinkID varchar(100) NOT NULL,
  MainObjectID varchar(100) NOT NULL,
  ImageID varchar(100) NOT NULL,
  ClassificationAttributeID varchar(100) NOT NULL,
  PositionAttributeID varchar(100) NOT NULL,
  Caption text NOT NULL,
  SortOrder int NOT NULL,
  PublishDate date NOT NULL,
  p_FileName varchar(255) NOT NULL,
  p_Width int NOT NULL,
  p_Height int NOT NULL,
  p_MimeType varchar(100) NOT NULL,
  p_FileSize int NOT NULL,
  p_Ratio float NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_ImageLink_ImageLinkID ON ImageLink USING btree(ImageLinkID);
CREATE INDEX Index_ImageLink_MainObjectID ON ImageLink USING btree(MainObjectID);


CREATE TABLE Name (
  NameID varchar(100) NOT NULL,
  Type varchar(1) NOT NULL,
  Name varchar(255) NOT NULL,
  KeyName varchar(255) NOT NULL,
  n_Attributes int NOT NULL,
  n_Associations int NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_Name_NameID ON Name USING btree(NameID);


CREATE TABLE Release (
  ReleaseID varchar(100) NOT NULL,
  WorkID varchar(100) NOT NULL,
  ReleaseDate date,
  UPC varchar(100) NOT NULL,
  MSRP float NOT NULL,
  Territory varchar(50) NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_Release_WorkID ON Release USING btree(WorkID);
CREATE INDEX Index_Release_ReleaseID ON Release USING btree(ReleaseID);
CREATE INDEX Index_Release_UPC ON Release USING btree(UPC);


CREATE TABLE Work (
  WorkID varchar(100) NOT NULL,
  Type varchar(1) NOT NULL,
  Title varchar(255) NOT NULL,
  KeyTitle varchar(255) NOT NULL,
  OriginalReleaseDate date,
  n_Attributes int NOT NULL,
  n_Associations int NOT NULL,
  Action varchar(1) NOT NULL
);
CREATE INDEX Index_Work_WorkID ON Work USING btree(WorkID);
CREATE INDEX Index_Work_KeyTitle ON Work USING btree(KeyTitle);

