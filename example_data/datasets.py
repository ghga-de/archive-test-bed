"""Sample datasets for testing."""

from ghga_event_schemas.pydantic_ import (
    MetadataDatasetFile,
    MetadataDatasetOverview,
    MetadataDatasetStage,
)

DATASET_OVERVIEW_EVENT = MetadataDatasetOverview(
    accession="test-dataset-1",
    stage=MetadataDatasetStage.DOWNLOAD,
    title="Test Dataset 1",
    description="The first test dataset",
    files=[
        MetadataDatasetFile(
            accession="file-id-1",
            description="The first file",
            file_extension=".json",
        ),
        MetadataDatasetFile(
            accession="file-id-2",
            description="The second file",
            file_extension=".csv",
        ),
        MetadataDatasetFile(
            accession="file-id-3",
            description="The third file",
            file_extension=".bam",
        ),
    ],
)  # pyright: ignore
