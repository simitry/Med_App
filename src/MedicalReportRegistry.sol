// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * Medical Report Verification Smart Contract
 *
 * This contract stores medical report hashes and metadata for verification purposes.
 * It allows doctors to publish reports and anyone to verify report integrity.
 */
contract MedicalReportRegistry {

    // Struct to store report data
    struct Report {
        bytes32 reportId;
        bytes32 pdfHash;
        string cid;  // IPFS Content Identifier
        bytes32 patientHash;  // Hashed patient data for privacy
        address doctor;
        uint256 timestamp;
    }

    // Mapping from report ID to report data
    mapping(bytes32 => Report) public reports;

    // Event emitted when a new report is published
    event ReportPublished(
        bytes32 indexed reportId,
        bytes32 pdfHash,
        string cid,
        bytes32 patientHash,
        address indexed doctor,
        uint256 timestamp
    );

    /**
     * Publish a new medical report to the blockchain
     *
     * @param _reportId Unique identifier for the report
     * @param _pdfHash SHA256 hash of the PDF file
     * @param _cid IPFS Content Identifier for the PDF
     * @param _patientHash Hashed patient information
     */
    function publishReport(
        bytes32 _reportId,
        bytes32 _pdfHash,
        string memory _cid,
        bytes32 _patientHash
    ) public {
        require(_reportId != bytes32(0), "Report ID cannot be zero");
        require(_pdfHash != bytes32(0), "PDF hash cannot be zero");
        require(bytes(_cid).length > 0, "CID cannot be empty");
        require(_patientHash != bytes32(0), "Patient hash cannot be zero");

        // Check if report already exists
        require(reports[_reportId].reportId == bytes32(0), "Report already exists");

        // Create new report
        Report memory newReport = Report({
            reportId: _reportId,
            pdfHash: _pdfHash,
            cid: _cid,
            patientHash: _patientHash,
            doctor: msg.sender,
            timestamp: block.timestamp
        });

        // Store report
        reports[_reportId] = newReport;

        // Emit event
        emit ReportPublished(
            _reportId,
            _pdfHash,
            _cid,
            _patientHash,
            msg.sender,
            block.timestamp
        );
    }

    /**
     * Get report data by report ID
     *
     * @param _reportId The report identifier
     * @return reportId, pdfHash, cid, patientHash, doctor, timestamp
     */
    function getReport(bytes32 _reportId) public view returns (
        bytes32,
        bytes32,
        string memory,
        bytes32,
        address,
        uint256
    ) {
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

    /**
     * Verify if a PDF hash matches the stored hash for a report
     *
     * @param _reportId The report identifier
     * @param _pdfHash The PDF hash to verify
     * @return True if hashes match, false otherwise
     */
    function verifyReport(bytes32 _reportId, bytes32 _pdfHash) public view returns (bool) {
        Report memory report = reports[_reportId];
        if (report.reportId == bytes32(0)) {
            return false;
        }
        return report.pdfHash == _pdfHash;
    }

    /**
     * Get the total number of reports (for enumeration if needed)
     * Note: This is not efficient for large numbers of reports
     */
    function getReportCount() public pure returns (uint256) {
        // In a real implementation, you might want to track this
        // For now, return 0 as we don't have enumeration
        return 0;
    }
}