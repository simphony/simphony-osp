# Contributing to SimPhoNy

Thank you for considering to improve SimPhoNy. We welcome your contribution!

**How to contribute?**
<div align="center">
  <table border="" cellpadding="10 px" cellspacing="5 px">
    <tbody>
      <tr>
        <td>
          <p align="center">
            <a href="#issues">Issues</a><br>
            🐛✨
          </p>
          <p align="center">
            Report <a href="#reporting-bugs">bugs</a>, propose <a href="#proposing-enhancements-or-suggesting-new-features">enhancements</a> or suggest <a href="#proposing-enhancements-or-suggesting-new-features">new features</a>
          </p>
        </td>
        <td>
          <p align="center">
            <a href="#code">Code</a><br>
            👨‍💻
          </p>
          <p align="center">
            Help develop SimPhoNy
          </p>
        </td>
      </tr>
      <tr>
        <td>
          <p align="center">
            <a href="https://github.com/simphony/docs">Documentation</a><br>
            📖
          </p>
          <p align="center">
            Help others understand how SimPhoNy works
          </p>
        </td>
        <td>
          <p align="center">
            <a href="#forum">Forum</a><br>
            💬
          </p>
          <p align="center">
            Participate in discussions and answer other user's questions
          </p>
        </td>
      </tr>
    </tbody>
  </table>
</div>

Remember that you must adhere to the [Contributor Covenant Code of Conduct](https://github.com/simphony/osp-core/blob/master/CODE_OF_CONDUCT.md) if you decide to make a contribution.

## Issues

### Reporting bugs

When you find that something is not working, you can submit a bug report. This section provides guidelines on how to submit your report in a way that helps maintainers understand the problem and reproduce it. Submitting a good bug report is a key to have issues solved quickly.

#### Before submitting a bug report

1. Consider what is the possible cause of your issue. Sometimes the source of a problem is in the least expected place. For example, it could be in the ontology that you are using, in the network connection or in the software that a SimPhoNy wrapper is interacting with.
2. Check the [Q&A](https://github.com/simphony/osp-core/discussions/categories/q-a) section of the [discussions page](https://github.com/simphony/osp-core/discussions). Someone else might have already experienced the same issue and got an answer on how to solve it.
3. Search for similar issues on the [issue board](https://github.com/simphony/osp-core/issues?q=is%3Aissue+sort%3Aupdated-desc+). The problem may already have been reported. If you are having issues while using a specific SimPhoNy wrapper, beware that each SimPhoNy Wrapper has its own issue board.

#### Submitting a bug report

Bug reports should be submitted on the [SimPhoNy issue board](https://github.com/simphony/osp-core/issues?q=is%3Aissue+sort%3Aupdated-desc+).  If you suspect that the issue has its origin in the code of a specific wrapper, rather than in SimPhoNy itself, visit the issue board of the wrapper instead. To create a new report, click the green [_"New"_](https://github.com/simphony/osp-core/issues/new/choose) button.

- [ ] Choose a meaningful title.
- [ ] Describing the problem in few words.
- [ ] Specify which version of the `simphony-osp` is affected. Use `pip show simphony-osp` to find out which version do you have installed. If the problem involves a wrapper, provide also the version of the wrapper.
- [ ] Explain how to reproduce the problem, step-by-step, and include a **minimal reproducible example**. A _minimal reproducible example_ is a code snippet where the issue can be observed. Include any additional files (e.g. an ontology file) that may be needed to execute the example. Skip the example _only if it is very difficult to provide it_.
- [ ] If the issue involves a crash or an exception, include the error message.

[Follow this link](https://github.com/simphony/osp-core/issues/740#issue-1107800007) to see an example of an accurate bug report. Providing a good bug report facilitates the work of the maintainers and enables them to solve the issue faster.

### Proposing enhancements or suggesting new features

Enhancements or new features should first be proposed on the [_"Ideas"_ section of the forum](https://github.com/simphony/osp-core/discussions/categories/ideas). 

When proposing, discussing, and designing a feature or enhancement on the forum, always aim to steer the discussion in a direction such that the following points are addressed:
- [ ] Motivation for the enhancement or the new feature.
- [ ] General overview of the enhancement or the new feature. Code snippets/mock-ups of how the feature or enhancement should work and behave.
- [ ] Estimation of the effort that implementing such enhancement or feature might involve. Technologies that could enable the implementation. This information helps the maintainers decide whether to implement a feature or enhancement, and to estimate the timeframe for a potential implementation.

After this discussion phase, when the maintainers deem it appropriate, the discussion on the forum can be closed and an issue referencing it can be created on the [issue board](https://github.com/simphony/osp-core/issues?q=is%3Aissue+sort%3Aupdated-desc+). The goal of this procedure is to separate discussion and design from implementation efforts. The issue is now ready to be worked on. The [_code section_](#Code) explains how to contribute to solve an issue.

## Code

Code contributions are generally aimed at fixing bugs and implementing enhancements or new features. The way to contribute code to the project are [pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests).

If you are unsure about where to start, check the issues tagged as [_newcomer task_](https://github.com/simphony/osp-core/issues?q=label%3A%22%F0%9F%91%A9%E2%80%8D%F0%9F%8E%93+newcomer+task%22+sort%3Acomments-desc). Such issues should either be simple to solve, or be a good entry point for understanding the codebase.

If you have a bugfix or have a feature/enhancement implementation that you want to contribute, please read [this page](https://simphony.readthedocs.io/en/latest/contribute.html) to understand how the code is organized, what is the meaning of the different git branches on the repository, and what automatic checks your code will have to pass in order to be accepted. After that, just fork the repository and make a new pull request.

Usually, there will be an issue associated with the specific bug to solve, or feature/enhancement to implement. Please add [closing keywords](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword) to your PR so that it becomes automatically linked to the corresponding issue.

In certain cases, however, you may submit a PR even if there is no associated issue. The most obvious examples are fixes for typos or improvement of docstrings. But also if you have a performance improvement that you can directly prove, or want to provide a fix for a bug that has not been spotted yet, you can skip the creation of an issue.

After you submit your pull request, a maintainer will review it. It is possible that additional work is needed before the maintainer can accept the PR. To make things smoother, please consider [allowing us to directly edit your PR](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/allowing-changes-to-a-pull-request-branch-created-from-a-fork), so that we can perform minor edits without having to wait for your feedback.

Of course, even if you are not a maintainer, you are also very welcome to comment on the pull requests submitted by other community members and give feedback to them.

## Documentation


## Forum

Feel free to participate on the [forum](https://github.com/simphony/osp-core/discussions)! There you may:

- Read [announcements](https://github.com/simphony/osp-core/discussions/categories/announcements) from the SimPhoNy team.
- Have [general discussions](https://github.com/simphony/osp-core/discussions/categories/general) about SimPhoNy.
- Propose [new features or enhancements](https://github.com/simphony/osp-core/discussions/categories/ideas). Please follow the guidelines provided on [this section](#proposing-enhancements-or-suggesting-new-features).
- [Ask other members of the community for help](https://github.com/simphony/osp-core/discussions/categories/q-a) in a [Q&A format](https://en.wikipedia.org/wiki/Q%26A_software).
- [Share how did you benefit from using SimPhoNy](https://github.com/simphony/osp-core/discussions/categories/show-and-tell) if you used SimPhoNy in your project. 
