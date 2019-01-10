# Contributing to Sugar Project

### Reporting Bugs

* **Ensure** the bug was not already reported! Try searching on GitHub under [Issues](https://github.com/sugarsack/sugar/issues).

* If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/sugarsack/sugar/issues/new). 
Be sure to include the following: 
  * Title
  * Clear description of the problem
  * Reproducer of the problem with clear steps
  * All relevant information as possible
  * Code sample or a use scenario, demonstrating the expected behavior that is not occurring.

### Writing a patch that fixes a bug

* Open a new GitHub pull request with the patch.

* Ensure the PR description clearly describes the problem and solution. Include the relevant issue number if applicable.

### Adding a new feature

``` important:: All features are added only to major releases!
```
Sugar Project does not accept feature additions in bug-fix branches. So all feature work should be
done only in the development master branch.

To formally propose a new feature, the proposal must take the form
of an RFC. To create an RFC, please do the following:
 
- Copy the template file found in the `rfc/` and rename it to `some-topic.md`.

- Fill the outline with the reasoning for the new feature.

- Add implementation details.

- Submit the written RFC via a pull-request

After this done, pull-request will be reviewed by the community. Once discussed and agreed upon, the RFC may be merged.

A merged RFC indicates that a feature has been accepted and may be implemented according to the description,
being available in an upcoming release of Sugar.

### "Who can write, writes the documentation!"

Sugar Project has two main sets of documentation:

  - The guides, which help you learn about it
  - The API, which serves as a reference.

You can help improve the guides by making them more coherent, consistent, or readable, adding missing information, correcting factual errors, fixing typos, or bringing them up to date with the latest edge.

To do so, make changes to Sugar Project guides source files (located here on Git repo). Then open a pull request to apply your changes to the master branch.

Thanks!
