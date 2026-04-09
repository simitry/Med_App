// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract DoctorRegistry {
    struct Doctor {
        bytes32 doctorId;
        bytes32 licenseHash;
        string metadataCid;
        bool isVerified;
        bool isActive;
        uint256 registeredAt;
        uint256 updatedAt;
    }

    address public owner;
    mapping(address => Doctor) private doctors;

    event DoctorRegistered(
        address indexed doctorWallet,
        bytes32 indexed doctorId,
        bytes32 licenseHash,
        string metadataCid,
        uint256 registeredAt
    );

    event DoctorStatusUpdated(
        address indexed doctorWallet,
        bool isVerified,
        bool isActive,
        uint256 updatedAt
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function registerDoctor(
        address doctorWallet,
        bytes32 doctorId,
        bytes32 licenseHash,
        string memory metadataCid
    ) public onlyOwner {
        require(doctorWallet != address(0), "Doctor wallet cannot be zero");
        require(doctorId != bytes32(0), "Doctor ID cannot be zero");
        require(licenseHash != bytes32(0), "License hash cannot be zero");

        Doctor storage doctor = doctors[doctorWallet];
        require(doctor.doctorId == bytes32(0), "Doctor already registered");

        doctors[doctorWallet] = Doctor({
            doctorId: doctorId,
            licenseHash: licenseHash,
            metadataCid: metadataCid,
            isVerified: true,
            isActive: true,
            registeredAt: block.timestamp,
            updatedAt: block.timestamp
        });

        emit DoctorRegistered(
            doctorWallet,
            doctorId,
            licenseHash,
            metadataCid,
            block.timestamp
        );
    }

    function updateDoctorStatus(
        address doctorWallet,
        bool isVerified,
        bool isActive
    ) public onlyOwner {
        Doctor storage doctor = doctors[doctorWallet];
        require(doctor.doctorId != bytes32(0), "Doctor not registered");

        doctor.isVerified = isVerified;
        doctor.isActive = isActive;
        doctor.updatedAt = block.timestamp;

        emit DoctorStatusUpdated(
            doctorWallet,
            isVerified,
            isActive,
            block.timestamp
        );
    }

    function getDoctor(address doctorWallet)
        public
        view
        returns (
            bytes32 doctorId,
            bytes32 licenseHash,
            string memory metadataCid,
            bool isVerified,
            bool isActive,
            uint256 registeredAt,
            uint256 updatedAt
        )
    {
        Doctor memory doctor = doctors[doctorWallet];
        require(doctor.doctorId != bytes32(0), "Doctor not registered");

        return (
            doctor.doctorId,
            doctor.licenseHash,
            doctor.metadataCid,
            doctor.isVerified,
            doctor.isActive,
            doctor.registeredAt,
            doctor.updatedAt
        );
    }

    function isDoctorInGoodStanding(address doctorWallet) public view returns (bool) {
        Doctor memory doctor = doctors[doctorWallet];
        return doctor.doctorId != bytes32(0) && doctor.isVerified && doctor.isActive;
    }
}
