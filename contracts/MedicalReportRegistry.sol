// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IDoctorRegistry {
    function isDoctorInGoodStanding(address doctorWallet) external view returns (bool);
}

contract MedicalReportRegistry {
    struct Report {
        bytes32 reportId;
        bytes32 pdfHash;
        string cid;
        bytes32 patientHash;
        address doctor;
        uint256 timestamp;
    }

    mapping(bytes32 => Report) public reports;
    IDoctorRegistry public doctorRegistry;

    event ReportPublished(
        bytes32 indexed reportId,
        bytes32 pdfHash,
        string cid,
        bytes32 patientHash,
        address indexed doctor,
        uint256 timestamp
    );

    constructor(address doctorRegistryAddress) {
        require(doctorRegistryAddress != address(0), "Doctor registry address cannot be zero");
        doctorRegistry = IDoctorRegistry(doctorRegistryAddress);
    }

    function publishReport(
        bytes32 _reportId,
        bytes32 _pdfHash,
        string memory _cid,
        bytes32 _patientHash
    ) public {
        require(doctorRegistry.isDoctorInGoodStanding(msg.sender), "Doctor integrity check failed");
        require(_reportId != bytes32(0), "Report ID cannot be zero");
        require(_pdfHash != bytes32(0), "PDF hash cannot be zero");
        require(bytes(_cid).length > 0, "CID cannot be empty");
        require(_patientHash != bytes32(0), "Patient hash cannot be zero");
        require(reports[_reportId].reportId == bytes32(0), "Report already exists");

        reports[_reportId] = Report({
            reportId: _reportId,
            pdfHash: _pdfHash,
            cid: _cid,
            patientHash: _patientHash,
            doctor: msg.sender,
            timestamp: block.timestamp
        });

        emit ReportPublished(
            _reportId,
            _pdfHash,
            _cid,
            _patientHash,
            msg.sender,
            block.timestamp
        );
    }

    function getReport(bytes32 _reportId)
        public
        view
        returns (
            bytes32,
            bytes32,
            string memory,
            bytes32,
            address,
            uint256
        )
    {
        Report memory report = reports[_reportId];
        require(report.reportId != bytes32(0), "Report not found");

        return (
            report.reportId,
            report.pdfHash,
            report.cid,
            report.patientHash,
            report.doctor,
            report.timestamp
        );
    }

    function verifyReport(bytes32 _reportId, bytes32 _pdfHash) public view returns (bool) {
        Report memory report = reports[_reportId];
        if (report.reportId == bytes32(0)) {
            return false;
        }

        return report.pdfHash == _pdfHash;
    }
}
